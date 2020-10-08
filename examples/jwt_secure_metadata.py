#!/usr/bin/env python3
#
# Copyright (c) 2018, Somia Reality Oy
# All rights reserved.

from base64 import b64decode, urlsafe_b64encode
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

    key = JWK(kty="oct", k=urlsafe_b64encode(key_secret).rstrip(b"=").decode())
    token = JWT(header=header, claims=claims)
    token.make_encrypted_token(key)
    return token.serialize()


if __name__ == "__main__":
    key_id = "50s7kbi8"
    key_secret = b64decode("VREhJeA+rubaab1ZuMzBdIg9BFPCcZcHL9w6zaY8yBg=")
    expires = time() + 60
    name = "Bob"
    metadata = {
        "User Profile": "https://example.invalid/registry?user=12345",
        "Relevant Info": "for the agent's eyes",
        "Lotto Numbers": [2, 3, 5, 7, 11, 13, 17],
    }

    output = create_secure_metadata(key_id, key_secret, expires, metadata)
    print(output)
