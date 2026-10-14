# Postgres Database

PostgreSQL database service for InnoDocApp and PIP-InnoDocAppAuthZENV1.0.

## Features

- Stores document metadata, security levels, and sources
- Provides data to PostgREST (PIP) for OPA policy evaluation
- `init.sql`: Initialization script for tables, views, and mock data

## Usage

1. **Build**

```sh
docker compose build postgres
```

3. **Run**

```sh
docker compose run postgres
```

## Data Model

- `nodes`: Documents and folders
- `document_seclevel`: Security levels per document
- `document_source`: Source/project per document
- `pip.document_attributes`: View for OPA/PIP integration
