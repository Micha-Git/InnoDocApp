# InnoDocApp
Reference implementation of InnoDocApp, demonstrating fine-grained, AuthZEN-based authorization using verifiable credentials (EUDI/SD-JWT), with Security Token Service (STS) integration, Open Policy Agent (OPA)/Rego policies, automated tests, and performance benchmarks.

For detailed documentation and setup instructions, see the main application [README.md](/innodocappauthzenv1.0-main/README.md).

The provided application configuration is optimized for performance testing and excludes the complexity of decentralized identity. In this configuration, verifiable credentials are not used; instead, JWTs issued by Keycloak are used for authentication and authorization.

To execute tests involving decentralized identity, an environment with an EUDI-compliant verifier and valid verifiable credentials must be available and properly configured.
