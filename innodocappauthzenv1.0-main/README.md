# InnoDocAppAuthZEN

This repository provides a modular environment for experimenting with document access control and authorization complying with the AuthZEN standard and using modern technologies such as Envoy, OPA, and JWT-based verifiable credentials. The architecture is designed for extensibility and conformance testing.

## Repository Structure

- **services/**
  - [innodocapp/](services/innodocapp/README.md): Main application service for document management.
  - [innodocapp-proxy/](services/innodocapp-proxy/README.md): Go-based proxy for the InnoDocApp, handling authentication and authorization requests.
  - [secure-token-service/](services/secure-token-service/README.md): Secure Token Service backend and UI for issuing JWTs based on VP claims.
  - [opa-proxy/](services/opa-proxy/README.md): Envoy proxy with Lua and OPA integration for policy enforcement.
  - [pdp/](services/pdp/README.md): Policy Decision Point (PDP) with Rego policies for access control.
  - [postgres/](services/postgres/README.md): PostgreSQL database initialization and configuration.
  - [tests/](services/tests/README.md): Integration and conformance tests for the environment.

- **jwt_generator/**
  - [README.md](jwt_generator/README.md): Tools for generating JWTs and key pairs.

- **umlet/**
  - Contains all relevant diagrams for the architecture.

## Quick Start

1. **Clone the repository:**

2. **Configure environment variables:**
   - Edit the `.env` file in the root directory to match your setup.
   - See [.env Configuration](#env-configuration) below for details on each variable.

3. **Build and run the services:**
   To deploy the whole architecture, Docker Compose is needed. The deployment can be started with

   ```sh
   docker compose up --build
   ```

   Each service contains its own Dockerfile and README with build/run instructions. See the linked READMEs above for details.

4. **Run tests:**
   The tests are run automatically when the whole architecture is deployed. For details on the developed tests, see [services/tests/README.md](services/tests/README.md).

## Documentation

- Each service and tool has its own detailed documentation in its respective directory.
- For JWT and key generation, see [jwt_generator/README.md](jwt_generator/README.md).

## .env Configuration

The `.env` file contains all environment variables needed to run the services. Below is a description of each variable:

### Database Configuration

- `DB_HOST`: PostgreSQL host
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `DB_CONNECTION_STRING`: Full PostgreSQL connection string for the application
- `DB_API_SCHEMA_NAME`: Schema name for API exposed for the PIP
- `DB_API_ANONYMOUS_ROLE`: Anonymous role for unauthenticated requests

### External Services

- `PIP_DOCUMENT_ATTRIBUTES_URL`: URL to the PIP service for document attributes
- `INNODOCAPP_PROXY_HOST`: URL to the InnoDocApp proxy service
- `INNODOCAPP_HOST`: URL to the InnoDocApp service (used for testing)
- `INNODOCAPP_UI`: URL to the InnoDocApp UI
- `UI_STS_AUTH_URL`: URL to the Secure Token Service UI entry point
- `STS_BACKEND`: URL to the Secure Token Service backend

### Policy Decision Point (OPA)

- `OPA_HOST`: URL to the OPA proxy service
- `OPA_EVALUATION_URL`: URL to the OPA evaluation endpoint
- `OPA_EVALUATIONS_URL`: URL to the OPA evaluations endpoint
- `OPA_RESOURCE_SEARCH_URL`: URL to the OPA resource search endpoint

### Secure Token Service (STS)

- `STS_PUBLIC_KEY_B64`: Base64-encoded PEM public key used by the proxy to verify JWT signatures

**Note:** When running with Docker Compose, use the service names as hostnames. When running locally, adjust these URLs accordingly.

---

For more details, explore the linked documentation in each subdirectory.
