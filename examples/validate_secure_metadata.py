#!/usr/bin/env python3
#
# Copyright (c) 2020, Somia Reality Oy
# All rights reserved.

# Installing dependencies:
#
# - Ubuntu/Debian: apt install python3-cryptography python3-jwcrypto
# - Using pip:     pip3 install cryptography jwcrypto

from argparse import ArgumentParser
from base64 import b64decode, urlsafe_b64decode, urlsafe_b64encode
from calendar import timegm
from datetime import datetime
from hashlib import sha512
from hmac import compare_digest
from json import dumps, loads
from time import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from jwcrypto.jwe import JWE
from jwcrypto.jwk import JWK

MAX_EXPIRE_WINDOW = 10 * 24 * 60 * 60  # 10 days


def assert_secure_metadata(master_key_type, master_key_id, master_key_secret, secure_metadata_str, time_now=None):
    if secure_metadata_str.count(".") < 2:
        assert master_key_type == "ninchat"
        return assert_ninchat_secure_metadata(master_key_id, master_key_secret, secure_metadata_str, time_now)
    else:
        assert master_key_type == "jwt"
        return assert_jwt_secure_metadata(master_key_id, master_key_secret, secure_metadata_str, time_now)


def assert_ninchat_secure_metadata(master_key_id, master_key_secret, secure_metadata_str, time_now=None):
    if "." in secure_metadata_str:
        key_id, msg_b64 = secure_metadata_str.split(".", 1)
        msg_iv = unpadded_urlsafe_b64decode(msg_b64)
    else:
        key_id, msg_b64 = secure_metadata_str.split("-", 1)
        msg_iv = b64decode(msg_b64)

    assert key_id == master_key_id

    key = b64decode(master_key_secret)
    msg_hashed = decrypt_aes_cbc(key, msg_iv)

    sha = sha512()
    digest = msg_hashed[:sha.digest_size]
    msg_padded = msg_hashed[sha.digest_size:]
    msg_json = msg_padded.rstrip(b"\0")
    sha.update(msg_json)
    assert compare_digest(sha.digest(), digest)

    msg_json_bytes = msg_json.decode()
    msg = loads(msg_json_bytes)
    assert_not_expired(msg["expire"], time_now)
    assert "user_id" not in msg
    return msg["metadata"]


def assert_jwt_secure_metadata(master_key_id, master_key_secret, secure_metadata_str, time_now=None):
    jwe = JWE()
    jwe.allowed_algs = ["dir", "A256GCM"]
    jwe.deserialize(secure_metadata_str)

    assert jwe.jose_header["alg"] == "dir"
    assert jwe.jose_header["enc"] == "A256GCM"
    assert jwe.jose_header["kid"] == master_key_id

    key = b64decode(master_key_secret)
    jwk = JWK(kty="oct", k=urlsafe_b64encode(key).rstrip(b"=").decode())
    jwe.decrypt(jwk)

    msg_json_bytes = jwe.payload.decode()
    msg = loads(msg_json_bytes)
    assert_not_expired(msg["exp"], time_now)
    assert "user_id" not in msg
    return msg["ninchat.com/metadata"]


def assert_not_expired(expire_time, time_now=None):
    if not time_now:
        time_now = time()

    assert isinstance(expire_time, (int, float))
    assert expire_time > time_now
    assert expire_time < time_now + MAX_EXPIRE_WINDOW


def decrypt_aes_cbc(key_bytes, iv_ciphertext):
    block_len = AES.block_size // 8
    assert len(iv_ciphertext) >= 2 * block_len
    assert (len(iv_ciphertext) % block_len) == 0
    iv = iv_ciphertext[:block_len]
    ciphertext = iv_ciphertext[block_len:]

    algo = AES(key_bytes)
    mode = CBC(iv)
    c = Cipher(algo, mode, default_backend())
    d = c.decryptor()
    plaintext = d.update(ciphertext)
    plaintext += d.finalize()
    return plaintext


def unpadded_urlsafe_b64decode(unpadded_str):
    unpadded_bytes = unpadded_str.encode()
    padded_bytes = unpadded_bytes + (b"", None, b"==", b"=")[len(unpadded_bytes) & 3]
    return urlsafe_b64decode(padded_bytes)


def main():
    time_format = "%Y-%m-%dT%H:%M:%SZ"
    time_example = datetime.utcnow().strftime(time_format)

    parser = ArgumentParser()
    parser.add_argument("--now", metavar="TIME", help="fake timestamp (UTC) for checking expiration (example: {})".format(time_example))
    parser.add_argument("master-key-type", help='"ninchat" or "jwt"')
    parser.add_argument("master-key-id", help="encryption key id")
    parser.add_argument("master-key-secret", help="base64-encoded encryption key (as received from Ninchat)")
    parser.add_argument("secure-metadata", help="the string to validate")
    args = parser.parse_args()

    metadata = assert_secure_metadata(
        getattr(args, "master-key-type"),
        getattr(args, "master-key-id"),
        getattr(args, "master-key-secret"),
        getattr(args, "secure-metadata"),
        timegm(datetime.strptime(args.now, time_format).utctimetuple()) if args.now else None,
    )

    print(dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
