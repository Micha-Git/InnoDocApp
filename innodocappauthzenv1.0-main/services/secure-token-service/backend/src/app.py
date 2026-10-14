from flask import Flask, request, jsonify, abort, redirect, make_response
from markupsafe import escape
from jwcrypto import jwk
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

import redis
import os
import requests
import base64
import json
import uuid
import time
import jsonata
import jwt
import hashlib

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_host=1,
    x_proto=1,
    x_port=1,
    x_prefix=1
)
app.config["DEBUG"] = True

# Environment variables
STS_PORT = int(os.environ["STS_PORT"])
STS_PUBLIC_KEY_B64 = os.environ["STS_PUBLIC_KEY_B64"]
STS_PRIVATE_KEY_B64 = os.environ["STS_PRIVATE_KEY_B64"]
STS_VALID_REDIRECT_URLS = os.environ["STS_VALID_REDIRECT_URLS"]
STS_VERIFIER_URL = os.environ["STS_VERIFIER_URL"]
STS_VERIFIER_DCQL_QUERY_JSON = os.environ["STS_VERIFIER_DCQL_QUERY_JSON"]
STS_VERIFIER_INIT_PATH = os.environ["STS_VERIFIER_INIT_PATH"]
STS_ISSUER = os.environ["STS_ISSUER"]
STS_AUDIENCE = os.environ["STS_AUDIENCE"]
STS_TOKEN_EXPIRATION = int(os.environ["STS_TOKEN_EXPIRATION"])

STS_KID = "45547204-3406-4a33-9b1e-a984eff6d940"

# TODO: Externalisieren
redis_session = redis.Redis(host='redis', port=6379, db=0)

OIDC_CONFIG_ENDPOINT = ".well-known/openid-configuration"
AUTHORIZATION_ENDPOINT = "protocol/openid-connect/auth"
TOKEN_ENDPOINT = "protocol/openid-connect/token"
END_SESSION_ENDPOINT = "protocol/openid-connect/logout"
JWKS_ENDPOINT = "protocol/openid-connect/certs"

@app.errorhandler(500)
def custom500(error):
    return jsonify({'message': error.description}), 500

def cors_headers(f):
    """Decorator to add CORS headers."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

    return decorated_function


@app.before_request
def handle_preflight():
    """Handle CORS preflight requests."""
    if request.method == "OPTIONS":
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response


@app.route("/")
@cors_headers
def index():
    return escape("OIDC Condig: /.well-known/openid-configuration")

@app.get("/" + OIDC_CONFIG_ENDPOINT)
@cors_headers
def config():
    base_url = request.url_root
    authorization_endpoint_url = f"{request.scheme}://{request.host}/{AUTHORIZATION_ENDPOINT}"
    token_endpoint_url = base_url + TOKEN_ENDPOINT
    end_session_endpoint_url = base_url + END_SESSION_ENDPOINT
    jwks_url = base_url + JWKS_ENDPOINT
    config = {"authorization_endpoint": authorization_endpoint_url, "token_endpoint": token_endpoint_url, "end_session_endpoint": end_session_endpoint_url, "jwks_uri": jwks_url}

    return jsonify(config)

@app.get("/" + JWKS_ENDPOINT)
@cors_headers
def jwks():
    pem_b64 = STS_PUBLIC_KEY_B64.replace("\n", "")
    pem_bytes = base64.b64decode(pem_b64)

    key = jwk.JWK.from_pem(pem_bytes)

    key.kid = STS_KID

    jwks = {"keys": [json.loads(key.export())]}

    return jsonify(jwks)


@app.get("/" + END_SESSION_ENDPOINT)
@cors_headers
def logout():
    allowed_urls = json.loads(STS_VALID_REDIRECT_URLS)
    redirect_url = request.args.get("post_logout_redirect_uri")
    if redirect_url in allowed_urls:
        return redirect(redirect_url)
    else:
        return jsonify({'message': 'post_logout_redirect_uri not whitelisted'}), 403

# EUDI endpoints

@app.get("/qrcode")
@cors_headers
def qrcode():
    payload = json.loads(STS_VERIFIER_DCQL_QUERY_JSON)
    payload["nonce"] = str(uuid.uuid4())
    try:
        response = requests.post(STS_VERIFIER_URL.rstrip("/") + "/" + STS_VERIFIER_INIT_PATH.lstrip("/"), json=payload, headers={"Accept": "image/png"})
        png_bytes = response.content
        qr_data_uri = "data:image/png;base64," + base64.b64encode(png_bytes).decode()
        transaction_id = response.headers.get("transaction-id")
        return jsonify(
            {
                "session_id": transaction_id,
                "qr_url": qr_data_uri,
                "status": "pending",
            }
        )
    except Exception as e:
        abort(500, "Verifier not reachable")

@app.get("/status")
@cors_headers
def status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"message": "session not found"}), 404
    try:
        url = STS_VERIFIER_URL.rstrip("/") + "/" + STS_VERIFIER_INIT_PATH.lstrip("/").rstrip("/") + "/" + session_id + "/events"
        response = requests.get(url)
        if response.status_code == 404:
            return jsonify({"message": "session not found"}), 404
        data = response.json()
        for e in data["events"]:
            if e.get("event") == "Wallet response posted":
                return jsonify({"status": "complete"})
        return jsonify({"status": "pending"})
    except Exception as e:
        abort(500, "Verifier not reachable")

@app.get("/issue")
@cors_headers
def issue():
    session_id = request.args.get("session_id")
    return_url = request.args.get("return_url")
    code_challenge = request.args.get("code_challenge")
    if not session_id or not return_url:
        return jsonify({"error": "session_id and return_url are required"}), 400

    try:
        url = STS_VERIFIER_URL.rstrip("/") + "/" + STS_VERIFIER_INIT_PATH.lstrip("/").rstrip("/") + "/" + session_id
        response = requests.get(url)
        data = response.json()

        # Get VP Token
        dcql_query = json.loads(STS_VERIFIER_DCQL_QUERY_JSON)
        dcql_id = dcql_query["dcql_query"]["credentials"][0]["id"]
        vp_token0 = data["vp_token"]
        vp_token1 = vp_token0[dcql_id]
        vp_token = vp_token1[0]

        # Get VP Claims
        url = STS_VERIFIER_URL.rstrip("/") + "/utilities/process/sdJwtVc"
        body = {"sd_jwt_vc": vp_token}
        response = requests.post(url, data=body)
        data = response.json()

    except Exception as e:
        abort(500, "Verifier not reachable")

    # Transform VP Claims
    transformation_file_path = "/app/JSONata/transformation.jsonata"

    with open(transformation_file_path, "r", encoding="utf-8") as transformation_file:
        transformation_expression_str = transformation_file.read()

    jsonata_expression = jsonata.Jsonata(transformation_expression_str)
    transformed_claims = jsonata_expression.evaluate(data)
    jwt = sign_jwt(transformed_claims)
    code = save_jwt(jwt, code_challenge)

    allowed_urls = json.loads(STS_VALID_REDIRECT_URLS)
    if return_url in allowed_urls:
        return redirect(return_url + "?code=" + code)
    else:
        return jsonify({'message': 'redirect_uri not whitelisted'}), 403

@app.post("/" + TOKEN_ENDPOINT)
@cors_headers
def token():
    code = request.form.get("code")
    redirect_uri = request.form.get("redirect_uri")
    code_verifier = request.form.get("code_verifier")

    raw_data = redis_session.get(code)
    if raw_data is None:
        return jsonify({'message': 'invalid code'}), 400
    data = json.loads(raw_data)
    code_challenge = data["code_challenge"]

    sha256 = hashlib.sha256(code_verifier.encode("ascii")).digest()
    calculated_challenge = base64.urlsafe_b64encode(sha256).decode("ascii").rstrip("=")

    if code_challenge != calculated_challenge:
        return jsonify({'message': 'incorrect code_challenge'}), 403

    allowed_urls = json.loads(STS_VALID_REDIRECT_URLS)
    if redirect_uri in allowed_urls:
        jwt = data["jwt"]
        redis_session.delete(code)
        return jsonify({"access_token": jwt, "expires_in": STS_TOKEN_EXPIRATION, "id_token": jwt})
    else:
        return jsonify({'message': 'redirect_uri not whitelisted'}), 403

def save_jwt(jwt: str, code_challenge: str):
    code = str(uuid.uuid4())
    data = {"jwt": jwt, "code_challenge": code_challenge}
    redis_session.set(code, json.dumps(data), ex=STS_TOKEN_EXPIRATION)
    return code

def sign_jwt(subject_claims: str):
    claims = {
        "iss": STS_ISSUER,
        "aud": STS_AUDIENCE,
        "iat": int(time.time()),
        "exp": int(time.time()) + STS_TOKEN_EXPIRATION,
        "subject": subject_claims,
    }
    try:
        pem_b64 = STS_PRIVATE_KEY_B64.replace("\n", "")
        pem_bytes = base64.b64decode(pem_b64)
        token = jwt.encode(claims, pem_bytes, algorithm="ES256")
        return token
    except Exception as e:
        abort(500, "Signing key type not supported")
    


app.run(host="0.0.0.0", port=STS_PORT)

