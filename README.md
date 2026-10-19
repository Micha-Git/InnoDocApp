# InnoDocApp
Reference implementation of InnoDocApp: fine-grained, AuthZEN-based authorization using verifiable credentials (EUDI/SD-JWT), with STS, OPA/Rego, tests and benchmarks.

The application provided application configuration are setup for the performance test runs excluding decentralized identity complexity. The application is configured to run without verifiable credentials using JWT tokens provided from Keycloak.

For runs with decentralized identity, an environment including an EUDI verifier, as well as valid verifiable credentials is required. 