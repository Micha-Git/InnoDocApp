import jwt 
import json
from typing_extensions import Annotated
import typer
from cryptography.hazmat.primitives import serialization
import datetime

app = typer.Typer()

@app.command()
def main(
    json_file: Annotated[str, typer.Argument(help="The file containing the JSON data to be encoded and signed")],
    private_key_file: Annotated[str, typer.Argument(help="The file containing the private key to be used to sign the JWT-encoded content")],
):
    with open(json_file) as jwtf: 
        json_data = json.load(jwtf)
    with open(private_key_file, "rb") as skf:
        key_data = skf.read()
        private_key = serialization.load_pem_private_key(key_data, password=None)

    if private_key.__class__.__name__ == "RSAPrivateKey":
        alg = "RS256"
    elif private_key.__class__.__name__ == "ECPrivateKey":
        alg = "ES256"
    else:
        raise ValueError("Unsupported key type: " + private_key.__class__.__name__ )

    token = jwt.encode(json_data, key=key_data, algorithm=alg)

    print("Generated JWT:")
    print(token)


if __name__ == "__main__":
    app()