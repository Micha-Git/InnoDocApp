# InnoDocApp Proxy

Go-based HTTP proxy for InnoDocApp.  
Acts as a Policy Enforcement Point (PEP), forwarding requests to OPA (Open Policy Agent) for authorization decisions using the AuthZEN model.

## Features

- **Reverse Proxy:** Forwards HTTP requests to the InnoDocApp backend.
- **Policy Enforcement:** Intercepts requests and sends authorization queries to OPA before proxying.
- **JWT Validation:** Verifies Bearer JWTs using the STS public key before asking OPA.
- **STS Redirects:** Returns a redirect URL for authentication when no token is present.
- **AuthZEN Integration:** Formats requests and interprets responses according to the AuthZEN information model.
- **Logging:** Logs incoming requests, authorization decisions, and PDP responses for auditing and debugging.

## Key Files

- `proxy.go`: Main Go-based proxy logic, including request interception, AuthZEN request construction, and OPA communication.
- `authzen/`: Go package for AuthZEN request/response and information model types.
- `go.mod`: Go module definition.

## Environment Variables

- `INNODOCAPP_HOST`: URL of the InnoDocApp backend service.
- `OPA_EVALUATION_URL`: URL of the OPA policy evaluation endpoint.
- `UI_STS_AUTH_URL`: URL of the Secure Token Service UI used for authentication.
- `UI_RETURN_URL_BASE`: Base URL for UI redirects (used to build return_url).
- `STS_PUBLIC_KEY_B64`: Base64-encoded PEM public key for verifying STS JWTs.

## Usage

1. **Build**

```sh
docker compose build innodocapp-proxy
```

1. **Run**

```sh
docker compose run innodocapp-proxy
```

1. **Proxy Behavior**
   - Receives HTTP requests on port `80`.
   - If the `Authorization` header is missing, responds `401` with a JSON body containing a `redirect_url` to the STS UI.
   - Extracts and validates the `Authorization` header (expects a Bearer JWT issued by the STS).
   - Constructs an AuthZEN-compliant authorization request.
   - Sends the request to OPA for a decision.
   - Forwards the request to the backend only if OPA allows it.

## Notes

- Requires OPA and InnoDocApp running and accessible on the same network.
- Designed for integration with AuthZEN-compliant policy and digital identity infrastructure.
- Logging is enabled for all major proxy and authorization events.

## See Also

- [OPA (Open Policy Agent)](https://www.openpolicyagent.org/)
- [AuthZEN Information Model](https://openid.net/specs/authorization-api-1_0.html#name-information-model)
