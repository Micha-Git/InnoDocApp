from flask import Flask, request, jsonify, abort
from markupsafe import escape
from model.subject import Subject
from pydantic import ValidationError

import json
import psycopg2
import os
import requests

app = Flask(__name__)

# Environment variables
DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]
OPA_EVALUATION_URL = os.environ["OPA_EVALUATION_URL"]
OPA_RESOURCE_SEARCH_URL = os.environ["OPA_RESOURCE_SEARCH_URL"]



@app.errorhandler(500)
def custom500(error):
    return jsonify({'message': error.description}), 500

def send_opa_request(query, endpoint):
    try:
        res = requests.post(endpoint, json=query)
        return res.json()
    except Exception as e:
        abort(500, str(e))


def check_document(subject: Subject, doc_id: str, action: str):
    query = {
        "subject": subject.model_dump(),
        "resource": {
            "type": "document",
            "id": doc_id
            },
        "action":{
            "name": action
        }
    }

    req = send_opa_request(query, OPA_EVALUATION_URL)
    return req["decision"]

def list_documents(subject: Subject, action):
    query = {
        "subject": subject.model_dump(),
        "resource": {"type": "document"},
        "action":{
            "name": action
            }
        }

    res_json = send_opa_request(query, OPA_RESOURCE_SEARCH_URL)
    return [item["id"] for item in res_json["results"]]

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )

def extract_subject_from_auth_header(auth_header) -> Subject:
    subject_dict = json.loads(auth_header)
    subject = Subject.model_validate(subject_dict)
    return subject


@app.route("/")
def index():
    return escape("Use /docs to get a list of all docs you are allowed to view or /doc/<path_to_document> to get the content of a document. Set the subject properties in the Authorization-Header, e.g., {\"type\":\"partner\",\"id\":\"john\",\"properties\":{\"sources\":[\"Horizon\",\"Orion\"],\"secLevel\":3}}")

@app.get("/docs2")
def docs2():

    document_ids = [4, 5, 6, 7, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 118, 119, 120]

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM file_paths WHERE file_id = ANY(%s);", (document_ids,))
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        
        result = [dict(zip(colnames, row)) for row in rows]

        cur.close()
        conn.close()
    except Exception as ex:
        abort(500, ex)

    return jsonify(result)

@app.get("/docs")
def docs():
    try:
        subject = extract_subject_from_auth_header(request.headers.get("Authorization"))
    except (ValidationError, json.JSONDecodeError, TypeError) as e:
        return jsonify({
            "error": "Authentication failed", 
            "details": e.errors() if isinstance(e, ValidationError) else str(e)
            }), 401

    document_ids = list_documents(subject, "can_read")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM file_paths WHERE file_id = ANY(%s);", (document_ids,))
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        
        result = [dict(zip(colnames, row)) for row in rows]

        cur.close()
        conn.close()
    except Exception as ex:
        abort(500, ex)

    return jsonify(result)

@app.get("/docs/<path:subpath>")
def doc(subpath):
    try:
        subject = extract_subject_from_auth_header(request.headers.get("Authorization"))
    except (ValidationError, json.JSONDecodeError, TypeError) as e:
        return jsonify({
            "error": "Authentication failed", 
            "details": e.errors() if isinstance(e, ValidationError) else str(e)
            }), 401
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT file_id FROM file_paths WHERE file_path=%s;", (subpath,))
        file_row = cur.fetchone()
        if not file_row:
            cur.close()
            conn.close()
            return jsonify({"error": "Document not found"}), 404

        file_id = file_row[0]

        if not check_document(subject, str(file_id), "can_read"):
            cur.close()
            conn.close()
            return jsonify({"error": "Access denied"}), 403

        cur.execute("SELECT file_path, content FROM file_paths WHERE file_path=%s;", (subpath,))
        entry = cur.fetchone()
        cur.close()
        conn.close()
        if entry is not None:
            colnames = [desc[0] for desc in cur.description]
            result = [dict(zip(colnames, entry))]
        else:
            return jsonify({"error": "Document not found"}), 404
    except Exception as ex:
        abort(500, "Database not reachable")

    if not result:
        return jsonify({"error": "Document not found"}), 404
    return jsonify(result)

app.run(host="0.0.0.0", port=80)
