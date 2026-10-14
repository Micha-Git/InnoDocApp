# InnoDocApp

This is the main business application for document management and sharing, implementing fine-grained, EUDI-compliant ABAC for secure document access.

## Features

- Document access and listing endpoints
- AuthZEN-compliant authorization requests
- Integration with OPA for policy decisions
- Browser UI for document browsing and search

## Structure

- `src/innodocapp/app.py`: Main application entrypoint
- `src/innodocapp/model/subject.py`: Subject model

## Configuration

The service expects the following environment variables (see [.env](.env) in the repository root):

- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: PostgreSQL connection parameters
- `OPA_EVALUATION_URL`: OPA evaluation endpoint (AuthZEN)
- `OPA_RESOURCE_SEARCH_URL`: OPA resource search endpoint

The application reads document metadata and contents from the `file_paths` view defined in [services/postgres/init.sql](services/postgres/init.sql). This view joins node paths with file content.

## Authorization Model

Requests must include an `Authorization` header containing a JSON-encoded subject that matches the `Subject` schema in [services/innodocapp/src/innodocapp/model/subject.py](services/innodocapp/src/innodocapp/model/subject.py):

Example subject payload:

```
{"type":"partner","id":"john","properties":{"sources":["Horizon","Orion"],"secLevel":3}}
```

The service forwards AuthZEN-style queries to OPA for:

- single-resource evaluation (`can_read` on a specific document)
- resource search (`can_read` across all documents)

When you call the backend through InnoDocApp-Proxy, the proxy validates the JWT, sends the AuthZEN request to OPA, and forwards the request to this service with an `Authorization` header that contains the JSON-encoded subject. Direct calls to the backend should still send the subject header explicitly.

## API Endpoints

- `GET /docs` — returns metadata for all documents the subject can read
- `GET /docs/<path>` — returns content for a single document path if allowed
- `GET /` — brief usage hint

## UI (ui-innodocapp)

The UI service provides a simple document browser and search interface. It calls the proxy endpoints (`/docs` and `/docs/<path>`) with a Bearer JWT and handles the redirect flow:

- On initial access, if the proxy responds `401` with a `redirect_url`, the UI redirects the browser to the Secure Token Service (STS).
- After verification, the STS redirects back with a `jwt_token` query parameter; the UI stores it in sessionStorage and uses it on subsequent requests.

## Usage

1. **Build**

   ```sh
   docker compose build innodocapp
   ```

2. **Run**
   ```sh
   docker compose up innodocapp
   ```

## Testing

Tests are located in `/services/tests`.
