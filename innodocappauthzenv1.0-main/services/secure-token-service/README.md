# Secure Token Service (STS)

The Secure Token Service issues short-lived JWTs after a VP verification step and redirects the browser back to the InnoDocApp UI with the token.

## Components

- `backend/`: Go API that issues JWTs and exposes QR/session endpoints.
- `frontend/`: Vue UI that starts the verification flow and redirects back to the caller.

## Flow

1. The InnoDocApp-Proxy returns a `redirect_url` when no token is present.
2. The UI loads the STS frontend with `return_url` as a query parameter.
3. The frontend requests a QR code (`/qrcode`). The backend initializes an EUDI verifier transaction and returns the `request_uri` as the QR URL.
4. The frontend polls status (`/status`).
5. When complete (after user presents credential to verifier), the frontend calls `/issue`.
6. The backend fetches the verified claims from the EUDI verifier, merges them with the subject data, and issues a JWT.
7. The backend sets a `jwt_token` cookie and redirects to `return_url` with `jwt_token` in the query string.

## EUDI Verifier Integration

This service is compatible with the [EUDI Verifier Endpoint](https://github.com/eu-digital-identity-wallet/eudi-srv-verifier-endpoint), which implements the OpenID4VP protocol for verifiable credential presentation.

### Workflow

1. **Initialize Transaction**: Backend calls `POST /ui/presentations` on the EUDI verifier with the DCQL query and parameters.
2. **Present QR Code**: The verifier returns a `request_uri` that is encoded in a QR code for the wallet to scan.
3. **Wallet Interaction**: User scans QR code with their EUDI Wallet and presents the requested credentials.
4. **Fetch Verified Claims**: Backend polls `GET /ui/presentations/{transaction_id}` to retrieve the verified claims.
5. **Issue JWT**: Backend merges verified claims with subject data and issues a JWT for application authentication.

### Supported Credential Formats

- **SD-JWT VC** (Selective Disclosure JWT Verifiable Credentials)
- **MSO MDoc** (Mobile Security Object Machine-Readable Documents)

The claim extraction logic automatically handles various response formats from the EUDI verifier.

## Backend Endpoints

- `GET /qrcode`: Starts a session and returns `session_id` and `qr_url`.
- `GET /status?session_id=...`: Returns `pending` or `complete`.
- `GET /issue?session_id=...&return_url=...`: Issues a JWT and redirects.
- `GET /health`: Health check.

## Environment Variables

### STS Configuration

- `STS_PRIVATE_KEY_PATH`: Path to the STS private key.
- `STS_PUBLIC_KEY_PATH`: Path to the STS public key.
- `SUBJECT_JSON_PATH`: Path to the subject JSON payload used in issued tokens.
- `STS_ISSUER`: JWT issuer (default: `secure-token-service`).
- `STS_AUDIENCE`: JWT audience (default: `innodocapp`).

### EUDI Verifier Configuration

- `STS_VERIFIER_URL`: Base URL for the EUDI verifier backend (e.g., `https://eudi.reiluk.dev/`).
- `STS_VERIFIER_INIT_PATH`: Verifier init transaction path (default: `/ui/presentations`).
- `STS_VERIFIER_RESPONSE_MODE`: Response mode to request (`direct_post` or `direct_post.jwt`).
- `STS_VERIFIER_JAR_MODE`: JAR mode to request (`by_value` or `by_reference`).
- `STS_VERIFIER_REQUEST_URI_METHOD`: Optional request_uri_method (`get` or `post`).
- `STS_VERIFIER_PROFILE`: Verifier profile (e.g., `openid4vp` or `haip`).
- `STS_VERIFIER_AUTHORIZATION_REQUEST_SCHEME`: Optional authorization request scheme (e.g., `openid4vp://`).
- `STS_VERIFIER_DCQL_QUERY_JSON`: DCQL query JSON string sent to the verifier init endpoint.

### EUDI Verifier Example Configuration

For the EUDI reference implementation at `https://eudi.reiluk.dev/`, use:

```bash
STS_VERIFIER_URL=https://eudi.reiluk.dev/
STS_VERIFIER_INIT_PATH=/ui/presentations
STS_VERIFIER_RESPONSE_MODE=direct_post
STS_VERIFIER_JAR_MODE=by_reference
STS_VERIFIER_PROFILE=openid4vp
STS_VERIFIER_DCQL_QUERY_JSON='{
  "credentials": [
    {
      "id": "0877f01d-b706-4c13-a16d-606139152426",
      "format": "dc+sd-jwt",
      "meta": {
        "vct_values": [
          "https://iss.cmiee.eu/ssi/vct/v1/f1833a94-c34b-45ce-9061-cbb10b017a1a/35b19ef1-eea7-4b48-9fbc-458e04567355"
        ]
      },
      "claims": [
        {
          "id": "7a283353-38de-4f88-ba55-5a24fb65d82b",
          "path": ["type"],
          "required": true
        },
        {
          "id": "59b6a3c9-d7f6-4306-b564-f02487563102",
          "path": ["id"],
          "required": true
        },
        {
          "id": "fc1795ff-549e-45be-a6ac-6e8306f624b4",
          "path": ["email"],
          "required": true
        },
        {
          "id": "4716c3c9-8f28-4ce2-a7e5-cb04e523beda",
          "path": ["name"],
          "required": true
        },
        {
          "id": "32d86d2a-cbad-4568-bf8b-07e7d4c24a2a",
          "path": ["properties"],
          "required": true
        },
        {
          "id": "68f167a4-955e-4315-994b-694b9990c573",
          "path": ["properties", "secLevel"],
          "required": true
        },
        {
          "id": "e41752f8-8297-4a77-b5de-193329d393fd",
          "path": ["properties", "sources"],
          "required": true
        }
      ]
    }
  ]
}'
```

## Usage

```sh
docker compose build secure-token-service ui-secure-token-service
```

```sh
docker compose up secure-token-service ui-secure-token-service
```
