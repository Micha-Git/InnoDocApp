#!/usr/bin/env python3

import os
import json
import time
import uuid
import base64
import requests
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Tuple, Optional

import hashlib
import jwt
from flask import Flask, request, jsonify, make_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global state
sessions = {}  # session_id -> timestamp
session_lock = {}

# Config
config = {
    "private_key_path": None,
    "public_key_path": None,
    "subject_json_path": None,
    "issuer": None,
    "audience": None,
    "verifier_base_url": None,
    "verifier_init_path": None,
    "verifier_response_mode": None,
    "verifier_jar_mode": None,
    "verifier_request_uri_method": None,
    "verifier_profile": None,
    "verifier_authorization_req_scheme": None,
    "verifier_dcql_query": None,
}

signing_key = None
subject_data = {}


def load_config():
    """Load configuration from environment variables."""
    config["private_key_path"] = os.getenv("STS_PRIVATE_KEY_PATH")
    config["public_key_path"] = os.getenv("STS_PUBLIC_KEY_PATH")
    config["subject_json_path"] = os.getenv("SUBJECT_JSON_PATH")
    config["issuer"] = os.getenv("STS_ISSUER")
    config["audience"] = os.getenv("STS_AUDIENCE")
    config["verifier_base_url"] = os.getenv("STS_VERIFIER_URL")
    config["verifier_init_path"] = os.getenv("STS_VERIFIER_INIT_PATH")
    config["verifier_response_mode"] = os.getenv("STS_VERIFIER_RESPONSE_MODE")
    config["verifier_jar_mode"] = os.getenv("STS_VERIFIER_JAR_MODE")
    config["verifier_request_uri_method"] = os.getenv("STS_VERIFIER_REQUEST_URI_METHOD")
    config["verifier_profile"] = os.getenv("STS_VERIFIER_PROFILE")
    config["verifier_authorization_req_scheme"] = (
        os.getenv("STS_VERIFIER_AUTHORIZATION_REQUEST_SCHEME")
    )
    config["verifier_dcql_query"] = os.getenv("STS_VERIFIER_DCQL_QUERY_JSON")

    required_fields = [
        "private_key_path",
        "public_key_path",
        "subject_json_path",
        "issuer",
        "audience",
        "verifier_base_url",
        "verifier_init_path",
        "verifier_response_mode",
        "verifier_jar_mode",
        "verifier_dcql_query",
    ]

    for field in required_fields:
        if not config[field]:
            raise ValueError(f"Missing required environment variable: {field.upper()}")

    # Parse DCQL query JSON
    try:
        config["verifier_dcql_query"] = json.loads(config["verifier_dcql_query"])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in STS_VERIFIER_DCQL_QUERY_JSON: {e}")

    logger.info("Configuration loaded successfully")


def load_keys():
    """Load private and public keys."""
    global signing_key

    with open(config["private_key_path"], "r") as f:
        signing_key = f.read()

    with open(config["public_key_path"], "r") as f:
        public_key = f.read()

    logger.info("Keys loaded successfully")


def load_subject():
    """Load subject data from JSON file."""
    global subject_data

    with open(config["subject_json_path"], "r") as f:
        subject_data = json.load(f)

    logger.info("Subject data loaded successfully")


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


@app.route("/qrcode", methods=["GET"])
@cors_headers
def handle_qrcode():
    """Initialize a verifier transaction and return QR code."""
    try:
        transaction_id, request_uri = init_verifier_transaction()
        record_session(transaction_id)

        return jsonify(
            {
                "session_id": transaction_id,
                "qr_url": request_uri,
                "status": "pending",
            }
        )
    except Exception as e:
        logger.error(f"Error in qrcode endpoint: {e}")
        return jsonify({"error": str(e)}), 502


@app.route("/status", methods=["GET"])
@cors_headers
def handle_status():
    """Check the status of a session."""
    session_id = request.args.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    if session_id not in sessions:
        return jsonify({"error": "session not found"}), 404

    # Check EUDI verifier events to determine status
    try:
        complete = check_verifier_status(session_id)
        status = "complete" if complete else "pending"
        return jsonify({"status": status})
    except Exception as e:
        logger.warning(f"Could not check verifier status: {e}")
        return jsonify({"status": "pending"})


@app.route("/issue", methods=["GET"])
@cors_headers
def handle_issue():
    """Issue a JWT after verifying the presentation."""
    session_id = request.args.get("session_id")
    return_url = request.args.get("return_url")

    if not session_id or not return_url:
        return jsonify({"error": "session_id and return_url are required"}), 400

    if session_id not in sessions:
        return jsonify({"error": "session not found"}), 404

    # Fetch verified claims from verifier
    try:
        verified_claims = fetch_verified_claims(session_id)
    except Exception as e:
        logger.error(f"Error fetching verified claims: {e}")
        return jsonify({"error": str(e)}), 502

    if not verified_claims:
        return jsonify({"error": "verifier returned no claims"}), 502

    # Merge verified claims with base subject
    merged_subject = merge_subjects(subject_data, verified_claims)
    normalize_subject_type(merged_subject)
    
    # Remove email field (it was already transformed to id)
    merged_subject.pop("email", None)

    # Issue JWT
    try:
        token = issue_jwt(merged_subject)
    except Exception as e:
        logger.error(f"Error issuing JWT: {e}")
        return jsonify({"error": "failed to issue token"}), 500

    # Redirect with token in URL
    response = make_response(
        {}, 302
    )  # Empty body, redirect status

    # Add token to return URL as query parameter
    separator = "&" if "?" in return_url else "?"
    final_url = f"{return_url}{separator}jwt_token={token}"

    response.headers["Location"] = final_url

    return response


@app.route("/health", methods=["GET"])
@cors_headers
def handle_health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


def init_verifier_transaction() -> Tuple[str, str]:
    """Initialize a transaction with the EUDI verifier."""
    # Use the entire DCQL query from config and only add/replace the nonce
    payload = dict(config["verifier_dcql_query"])
    payload["nonce"] = generate_nonce()

    init_url = (
        config["verifier_base_url"].rstrip("/") + config["verifier_init_path"]
    )
    logger.info(f"Initializing EUDI verifier transaction at {init_url}")

    response = requests.post(
        init_url, json=payload, timeout=15, headers={"Accept": "image/png"}
    )

    if response.status_code < 200 or response.status_code >= 300:
        raise Exception(
            f"EUDI verifier init failed ({response.status_code}): {response.text}"
        )

    transaction_id = response.headers.get("transaction-id")
    if not transaction_id:
        raise Exception("EUDI verifier response missing transaction-id header")

    # Convert PNG to data URI
    png_bytes = response.content
    qr_data_uri = "data:image/png;base64," + base64.b64encode(png_bytes).decode()

    logger.info(f"EUDI verifier transaction initialized: {transaction_id}")
    return transaction_id, qr_data_uri


def check_verifier_status(transaction_id: str) -> bool:
    """Check if the verifier has received the wallet response."""
    url = (
        config["verifier_base_url"].rstrip("/")
        + f"/ui/presentations/{transaction_id}/events"
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logger.warning(f"Failed to fetch verifier events: {response.status_code}")
            return False

        data = response.json()
        events = data.get("events", [])

        for event in events:
            if event.get("event") == "Wallet response posted":
                return True

        return False
    except Exception as e:
        logger.warning(f"Error checking verifier status: {e}")
        return False


def fetch_verified_claims(transaction_id: str) -> Dict[str, Any]:
    """Fetch verified claims from the EUDI verifier."""
    url = (
        config["verifier_base_url"].rstrip("/")
        + f"/ui/presentations/{transaction_id}"
    )

    logger.info(f"Fetching verified claims from EUDI verifier: {url}")

    response = requests.get(url, timeout=15)

    if response.status_code < 200 or response.status_code >= 300:
        raise Exception(
            f"EUDI verifier presentation fetch failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    vp_token = data.get("vp_token")

    if not vp_token:
        raise Exception("No vp_token in response")

    # Extract and decode claims from SD-JWT
    claims = extract_claims_from_vp_token(vp_token)

    logger.info(f"Extracted claims from EUDI verifier response:\n{json.dumps(claims, indent=2)}")

    return claims


def flatten_sd_jwt_strings(data: Any) -> list:
    """Recursively extract all SD-JWT strings from nested structures."""
    strings = []
    
    if isinstance(data, str):
        strings.append(data)
    elif isinstance(data, list):
        for item in data:
            strings.extend(flatten_sd_jwt_strings(item))
    elif isinstance(data, dict):
        for value in data.values():
            strings.extend(flatten_sd_jwt_strings(value))
    
    return strings


def decode_disclosure(disclosure_str: str) -> Tuple[str, str, Any]:
    """Decode an SD-JWT disclosure string.
    
    Returns: (hash, claim_name, claim_value)
    
    Disclosure formats:
    - Named claim: [salt, claim_name, claim_value] (3 elements)
    - Array item: [salt, claim_value] (2 elements) - returns hash, None, value
    """
    try:
        # Skip JWT-format disclosures (KB-JWT)
        if disclosure_str.startswith('eyJ'):
            return None, None, None
        
        # Hash is the base64url of the disclosure itself (without padding)
        import hashlib
        disclosure_bytes = disclosure_str.encode('utf-8')
        hash_bytes = hashlib.sha256(disclosure_bytes).digest()
        disclosure_hash = base64.urlsafe_b64encode(hash_bytes).decode().rstrip('=')
        
        # Add padding if needed for decoding
        padding = 4 - len(disclosure_str) % 4
        if padding != 4:
            disclosure_str += '=' * padding
        
        decoded = base64.urlsafe_b64decode(disclosure_str)
        parsed = json.loads(decoded)
        
        if not isinstance(parsed, list):
            logger.warning(f"Disclosure is not a list: {type(parsed)}")
            return None, None, None
        
        # Format: [salt, claim_name, claim_value] or [salt, claim_value]
        if len(parsed) == 3:
            # Named claim
            return disclosure_hash, parsed[1], parsed[2]
        elif len(parsed) == 2:
            # Array item - value without a claim name
            return disclosure_hash, None, parsed[1]
        else:
            logger.warning(f"Disclosure has unexpected length {len(parsed)}: {parsed}")
            return None, None, None
    except Exception as e:
        logger.warning(f"Failed to decode disclosure: {e}")
        return None, None, None


def resolve_disclosure_references(value: Any, disclosures_map: Dict[str, Any]) -> Any:
    """Recursively resolve disclosure references (\"...\" keys) with actual values."""
    if isinstance(value, dict):
        # Check if this is a disclosure reference
        if "..." in value and len(value) == 1:
            ref_hash = value["..."]
            if ref_hash in disclosures_map:
                return resolve_disclosure_references(disclosures_map[ref_hash], disclosures_map)
            return value
        
        # Recursively process dict values
        return {k: resolve_disclosure_references(v, disclosures_map) for k, v in value.items()}
    elif isinstance(value, list):
        # Recursively process list items
        return [resolve_disclosure_references(item, disclosures_map) for item in value]
    else:
        return value


def extract_claims_from_vp_token(vp_token: Dict[str, Any]) -> Dict[str, Any]:
    """Extract claims from the vp_token by decoding SD-JWTs."""
    all_claims = {}

    # Recursively extract all SD-JWT strings from vp_token (handles any nesting)
    sd_jwt_strings = flatten_sd_jwt_strings(vp_token)
    
    logger.info(f"Found {len(sd_jwt_strings)} SD-JWT string(s) in vp_token")

    # Process all SD-JWTs
    for sd_jwt_str in sd_jwt_strings:
        try:
            logger.info(f"Decoding SD-JWT: {sd_jwt_str[:80]}...")

            # SD-JWT format: header.payload.signature~disclosure1~disclosure2...
            parts = sd_jwt_str.split('~')
            jwt_part = parts[0]
            disclosures = parts[1:] if len(parts) > 1 else []
            
            logger.info(f"Found disclosures in SD-JWT: {disclosures}")
            
            # Decode JWT without verification
            claims = jwt.decode(jwt_part, options={"verify_signature": False})

            # Build a map of disclosure hashes to values
            disclosures_map = {}
            for i, disclosure in enumerate(disclosures):
                disclosure_hash, claim_name, claim_value = decode_disclosure(disclosure)
                if disclosure_hash:
                    disclosures_map[disclosure_hash] = claim_value
                    if claim_name:
                        logger.info(f"Disclosure {i}: hash={disclosure_hash}, claim={claim_name}")
                    else:
                        logger.info(f"Disclosure {i}: hash={disclosure_hash}, array_item={claim_value}")
                else:
                    logger.warning(f"Failed to decode disclosure {i}")

            logger.info(f"Built disclosures_map with {len(disclosures_map)} entries: {list(disclosures_map.keys())}")
            
            # Add named disclosed claims to claims dict
            for i, disclosure in enumerate(disclosures):
                disclosure_hash, claim_name, claim_value = decode_disclosure(disclosure)
                if disclosure_hash and claim_name:
                    claims[claim_name] = claim_value
                    logger.info(f"Added claim to dict: {claim_name}")

            # Resolve all disclosure references in the claims
            for key, value in claims.items():
                resolved = resolve_disclosure_references(value, disclosures_map)
                if resolved != value:
                    logger.info(f"Resolved references in claim '{key}'")
                claims[key] = resolved

            # Log the disclosures_map keys for debugging
            logger.info(f"Available disclosure hashes: {', '.join(disclosures_map.keys())}")

            raw_claims_json = json.dumps(claims, indent=2)
            logger.info(f"Raw claims before transformation:\n{raw_claims_json}")

            # Transform claims
            transformed = transform_claims(claims)

            transformed_json = json.dumps(transformed, indent=2)
            logger.info(f"Transformed claims:\n{transformed_json}")

            # Merge claims
            for key, val in transformed.items():
                all_claims[key] = val

        except Exception as e:
            logger.error(f"Failed to decode SD-JWT: {e}")
            import traceback
            traceback.print_exc()
            continue

    return all_claims


def transform_claims(raw_claims: Dict[str, Any]) -> Dict[str, Any]:
    """Transform and structure the claims from the verifier.
    
    Only keeps: id, type, name, and properties (with secLevel and sources).
    Transforms email to id. Filters out: _sd, _sd_alg, iat, exp, nbf, iss, cnf, vct, status, etc.
    """
    transformed = {}
    properties = {}
    
    # Whitelist of allowed claim names
    allowed_claims = {"id", "type", "name"}

    for key, value in raw_claims.items():
        if key == "secLevel":
            properties["secLevel"] = value
        elif key == "sources":
            properties["sources"] = value
        elif key == "email":
            # Transform email to id
            transformed["id"] = value
        elif key == "properties":
            if isinstance(value, dict):
                # Only include allowed keys from properties (filter out _sd, _sd_alg, etc.)
                for prop_key, prop_value in value.items():
                    if prop_key not in ("_sd", "_sd_alg"):
                        properties[prop_key] = prop_value
        elif key in allowed_claims:
            transformed[key] = value
        # All other fields (_sd, _sd_alg, iat, exp, nbf, iss, cnf, vct, status, etc.) are filtered out

    if properties:
        transformed["properties"] = properties

    return transformed


def merge_subjects(
    base: Dict[str, Any], claims: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge base subject with verified claims."""
    merged = dict(base)
    merged.update(claims)
    return merged


def normalize_subject_type(subject: Dict[str, Any]):
    """Normalize the subject type based on credential type.
    
    Maps credential types to subject.type:
    - "Document Partner Access Credential" → "partner"
    - "Document Project Manager Access Credential" → "project manager"
    """
    credential_type = extract_credential_type(subject)

    if credential_type == "Document Partner Access Credential":
        subject["type"] = "partner"
    elif credential_type == "Document Project Manager Access Credential":
        subject["type"] = "project manager"
    else:
        subject.pop("type", None)


def extract_credential_type(subject: Dict[str, Any]) -> Optional[str]:
    """Extract the credential type from the subject."""
    if "credential" in subject and isinstance(subject["credential"], dict):
        cred_type = subject["credential"].get("type")
        if isinstance(cred_type, str):
            return cred_type
        elif isinstance(cred_type, list) and len(cred_type) > 0:
            return cred_type[0]

    subject_type = subject.get("type")
    if isinstance(subject_type, str):
        return subject_type
    elif isinstance(subject_type, list) and len(subject_type) > 0:
        return subject_type[0]

    return None


def issue_jwt(subject: Dict[str, Any]) -> str:
    """Issue a JWT with the given subject claims."""
    claims = {
        "iss": config["issuer"],
        "aud": config["audience"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 900,  # 15 minutes
        "subject": subject,
    }

    # Log decoded claims
    claims_json = json.dumps(claims, indent=2)
    logger.info(f"JWT Claims (decoded):\n{claims_json}")

    # Try RS256 first, fall back to ES256 if key is EC
    try:
        token = jwt.encode(claims, signing_key, algorithm="RS256")
    except Exception as e:
        if "ECPrivateKey" in str(e) or "EC" in str(e):
            logger.info("Using ES256 algorithm for EC key")
            token = jwt.encode(claims, signing_key, algorithm="ES256")
        else:
            raise
    
    # Log encoded token
    logger.info(f"JWT Token (encoded):\n{token}")
    
    return token


def generate_nonce() -> str:
    """Generate a random nonce."""
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode().rstrip("=")


def record_session(session_id: str):
    """Record a new session."""
    sessions[session_id] = time.time()


if __name__ == "__main__":
    # Load configuration
    load_config()
    load_keys()
    load_subject()

    # Run Flask app
    app.run(host="0.0.0.0", port=80, debug=False)
