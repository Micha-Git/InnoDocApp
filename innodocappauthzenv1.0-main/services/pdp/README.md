# Policy Decision Point (PDP)

This service contains the Open Policy Agent (OPA) policies for InnoDocApp.

## Structure

- `evaluation.rego`: Main AuthZEN-compliant evaluation policy
- `evaluations.rego`: Batch evaluation logic
- `resource_search.rego`: Resource listing/search policy
- `policy_rules/`: Document, endpoint, and subject policy rules
- `utils/`: Utility modules (e.g., PIP integration)

## Policy Evaluation Endpoints

The PDP exposes the following main AuthZEN-compliant endpoints:

- **`/v1/data/evaluation`** - Evaluates a single authorization request and returns allow/deny decision with obligations
- **`/v1/data/evaluations`** - Evaluates a batch of authorization requests and returns a list of allow/deny decision with obligations depending on the selected evaluation mode
- **`/v1/data/resource_search`** - Searches for resources accessible to a subject based on their credentials and policies

These endpoints are accessed through the OPA Proxy via:

- `POST /access/v1/evaluation` → routes to `/v1/data/evaluation`
- `POST /access/v1/evaluations` → routes to `/v1/data/evaluations`
- `POST /access/v1/resource_search` → routes to `/v1/data/resource_search`

## Usage

Mount this directory into the OPA container:

1. **Build**

```sh
docker compose build pdp
```

2. **Mount**
   OPA will load all `.rego` files for policy evaluation.

```yaml
volumes:
  - ./services/pdp:/policies
```

3. **Run**

```sh
docker compose run pdp
```
