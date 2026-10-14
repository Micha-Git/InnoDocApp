# Generate allowed key pair for SecureTokenService 
openssl ecparam -name prime256v1 -genkey -noout -out sts_private_key.pem
openssl ec -in sts_private_key.pem -pubout -out unallowed_public_key.pem

# Generate key pair for unallowed signers
openssl ecparam -name prime256v1 -genkey -noout -out unallowed_private_key.pem
openssl ec -in unallowed_private_key.pem -pubout -out unallowed_public_key.pem
