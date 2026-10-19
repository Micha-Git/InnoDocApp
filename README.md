# InnoDocApp
Reference implementation of InnoDocApp: fine-grained, AuthZEN-based authorization using verifiable credentials (EUDI/SD-JWT), with STS, OPA/Rego, tests and benchmarks.

The application is documented in the main application [README.md](/innodocappauthzenv1.0-main/README.md).

The application provided application configuration are setup for the performance test runs excluding decentralized identity complexity. The application is configured to run without verifiable credentials using JWT tokens provided from Keycloak.

For runs with decentralized identity, an environment including an EUDI verifier, as well as valid verifiable credentials is required. 