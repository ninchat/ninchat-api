#!/usr/bin/env python3

from time import time

from jwcrypto.jwk import JWK
from jwcrypto.jwt import JWT


def create_secure_metadata(key_id, key_secret, expires, metadata):
    header = {
        "alg": "dir",
        "enc": "A256GCM",
        "kid": key_id,
    }

    claims = {
        "exp": int(expires),
        "ninchat.com/metadata": metadata,
    }

    key = JWK(kty="oct", k=key_secret)
    token = JWT(header=header, claims=claims)
    token.make_encrypted_token(key)
    return token.serialize()


if __name__ == "__main__":
    key_id = "50s7kbi8"
    key_secret = "VREhJeA-rubaab1ZuMzBdIg9BFPCcZcHL9w6zaY8yBg"
    expires = time() + 60
    name = "Bob"
    metadata = {
        "User Profile": "https://example.invalid/registry?user=12345",
        "Relevant Info": "for the agent's eyes",
        "Lotto Numbers": [2, 3, 5, 7, 11, 13, 17],
    }

    output = create_secure_metadata(key_id, key_secret, expires, metadata)
    print(output)
