# JWT Generator

This tool provides a command-line interface (CLI) for generating signed JWTs.

## Features

- Generate signed JWTs from a [subject JSON file](./subject.json).
- Sign JWTs using a provided private key.
- Output: standardized signed JWT
- Use pre-generated keys and JWT examples for testing.

## Usage

### 1. Install Dependencies

Install the required Python dependencies using `pip`:

```sh
python -m venv .venv
source .venv/bin/activate
pip install .
```

The commands above create a virtual environment in python and install all dependencies inside it. After executing them, the terminal will probably display a (.venv), because it's in a virtual environment where python can access the dependencies. The virtual enviroment can be exited with the command

```sh
deactivate
```

The dependencies can be removed by removing the created virtual environment (.venv folder):

```sh
rm -rf .venv
```

### 2. Generate Cryptographic Key Pairs

Before generating JWTs, you need to generate cryptographic key pairs (private and public keys). The repository includes pre-generated key pairs under `./keys` (see [pre-generated keys](#pre-generated-keys)) as well as the `generate_key_pairs.sh` script for this purpose.

Run the script to generate all required keys:

```sh
bash generate_key_pairs.sh
```

This will generate the following key pairs in the current directory (not in the `keys/` directory):

- `sts_private_key.pem` and `sts_public_key.pem` - Keys for the Secure Token Service (STS) to sign and verify JWTs
- `unallowed_private_key.pem` and `unallowed_public_key.pem` - Test keys for unauthorized signers

The keys use the NIST Prime256v1 (P-256) elliptic curve for EC signature generation.

**Note:** For production environments, securely manage and store these private keys. Do not commit them to version control.

### 3. Display Command-Line Help

Show the CLI help for the JWT generator script:

```sh
python src/generate_jwt.py --help
```

This will display usage instructions and available options.

### 4. Generate a Signed JWT

To generate a signed JWT, invoke the script with your JSON file and the generated private key:

```sh
python src/generate_jwt.py subject.json keys/sts_private_key.pem
```

This will output a signed signed JWT.

## Pre-generated Keys

The repository includes pre-generated STS and unallowed key pairs in `keys/` for quick testing. The JWT payloads are based on `subject.json`.

## Pre-generated JWTs

See `pre_generated_JWTs.md` for ready-to-use examples of:

- A valid JWT signed by `sts_private_key.pem`
- An intentionally corrupted JWT (prefixed)
- A JWT signed with `unallowed_private_key.pem`
