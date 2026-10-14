# OPA Proxy

Envoy-based proxy for transforming and forwarding AuthZEN-compliant requests to OPA.

## Features

- Lua script for JSON transformation
- Handles wrapping/unwrapping of OPA input/output
- Can be used as a sidecar or gateway in front of OPA

## Usage

1. **Build**

```sh
docker compose build opa-proxy
```

1. **Run**

```sh
docker compose run opa-proxy
```

### Key Files

- `envoy.yaml`: Envoy configuration with routing rules for the AuthZEN evaluation and resource search endpoints
- `transform.lua`: Lua transformation script that wraps/unwraps JSON payloads using the lua-cjson library

## Configuration Details

**Envoy Configuration (envoy.yaml):**

- Listens on port 80 for inbound HTTP requests
- Routes `/access/v1/evaluation` requests to the OPA service, rewriting the path to `/v1/data/evaluation`
- Routes `/access/v1/resource_search` requests to OPA, rewriting to `/v1/data/resource_search`
- Applies Lua filter for request/response transformation

**Lua Transform (transform.lua):**

- Wraps incoming JSON request bodies into `{ input: <request> }` format expected by OPA
- Unwraps OPA responses for AuthZEN compliance
- Handles edge cases and invalid JSON gracefully
- Requires lua-cjson library (included in the Dockerfile)

## Requirements

- Envoy
- OPA running and accessible
