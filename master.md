Ninchat Master Keys
===================

This document describes the signing and encryption which may be used with some
[Ninchat API](api.md) actions.

Copyright &copy; 2015-2017 Somia Reality Oy.  All rights reserved.


### Contents

- [Creating Keys](#creating-keys)
- [Action Signatures](#action-signatures)
- [Secure Metadata](#secure-metadata)
- [Available Implementations](#available-implementations)


### Associated documents

- [Ninchat Puppets](puppet.md)
- [Ninchat API](api.md)


Creating Keys
=============

The required keys can be created in two ways:

- While logged in at [Ninchat](https://ninchat.com/), go to
  `https://ninchat.com/#/x/settings/masterkeys`.
- Using the [`create_master_key`](api.md#create_master_key) API action, with
  the `master_key_type` parameter set to "ninchat".

By default a master key may be used for the following things:

- Authentication and control of puppet users.
- Authorizing access to the master user's resources (such as channels).

A master key may optionally be specific to a realm (aka. organization).  Such
keys differ from the non-specific ones in the following ways:

- They may not be used with puppets.
- They authorize access only to the specific realm's resources.
- Also the realm's operators may create and delete the keys.


Action Signatures
=================

A signature is formed from the following inputs:

- Master key id and secret
- Action name and optional parameters
- Expiration time in seconds since 1970-01-01 00:00 UTC
- Cryptographically secure pseudorandom nonce

The following standard algorithms are used:

- JSON serialization
- HMAC digest using SHA-512 hash function
- Base64 encoding


### Signature format

The signature is an ASCII string formed of four or five tokens, delimited by
dashes ("-"):

1. Master key id
2. Expiration time as a decimal string
3. ASCII nonce (must not contain dashes)
4. Base64-encoded HMAC-SHA512 digest
5. Optional mode flag: the literal "1" string

An example signature:

	22nlihvg-1444077534-EGk2DnQT-sVcP4GBueJKRe+hLq7619MjhKZA/t5NIpm/6MgQLnmTm9O2A3WWV
	YtpDn99rgq7iALqnGnGY/wihFFiO75ddmA==-1


### Authentication key

The master key secret (acquired from Ninchat) is base64-encoded.  It must be
decoded to get the key for the HMAC algorithm.


### Digested input

The HMAC digest is calculated from a JSON-serialized array.  The array contains
the action name and parameters, the expiration time (integer) and the nonce as
key-value pairs (= arrays with two items).  The array must be sorted by the
key, and the JSON encoding must use minimal whitespace (= only in string
literals).

An example JSON array:

	[["action","create_session"],["expire",1444077534],["nonce","ak/7LQ2uS0s="]]


### Action parameters

The parameters required for the digest input depend on the action and desired
mode of operation.

#### [`create_session`](api.md#create_session)

1. A new puppet user is created by default.  The optional `puppet_attrs`
   parameter is supported.

2. If the `user_id` parameter is specified, an existing puppet user is logged
   in.  (Note that the mode flag is not used.)

#### [`join_channel`](api.md#join_channel)

The `channel_id` parameter is required, and the optional `member_attrs`
parameter is supported.

1. Any user may use the signature by default.

2. If the `user_id` parameter is specified, only that user may use the
   signature.  The mode flag must be specified in the signature.


Secure Metadata
===============

An encrypted metadata property is formed from the following inputs:

- Master key id and secret
- Metadata (key-value pairs) to be secured
- Optional target user id
- Expiration time in seconds since 1970-01-01 00:00 UTC
- Cryptographically secure pseudorandom initialization vector (IV)

The following standard algorithms are used:

- JSON serialization
- SHA-512 hash function
- AES-256 encryption in CBC mode
- Base64 encoding


### Encrypted format

The result is an ASCII string formed of two tokens, delimited by a dash ("-"):

1. Master key id
2. Base64-encoded concatenation of the following:
   1. IV used during encryption
   2. AES-256-CBC ciphertext

An example:

	22nlihvg-mONwgi61ZoInzc3E2l2WdFtZ8L0dy9PVaNjshFvw8KeZQDEqYbrTYrnEECG9kApqWKefcwUM
	0zDfUno99xWl6Tas6tP7g2lx654uMhg0qRODDSfeX3f2a5p0mgTYLHd9b8RUPgVO0L9QBC4Y2gKC49xtV
	fmAyN76X1q28byGJW7c8xoRI7DnwBDU/hW8w73IYBIh2ww8uF5lxSivhdNag3grIqsDFDmvixOCuCV6Ff
	+ZVLxgIAt7p3dNFF9QwH7cH1F3FLWUqeBotuiYVa6Znw==


### Encryption key

The master key secret (acquired from Ninchat) is base64-encoded.  It must be
decoded to get the AES cipher key.


### Plaintext

The input data for the AES encryption is a concatenation of the following:

1. SHA-512 hash of 2. as a binary digest
2. JSON-serialized object
3. Optional padding (binary zeroes)

The JSON object must contain at least the `expire` (number) and `metadata`
(object) properties.  It may also contain the `user_id` (string) property,
which causes the target user to be checked.

An example JSON object:

	{
		"expire": 1444077534,
		"metadata": {
			"Foo": "bar",
			"Baz": "quux"
		},
		"user_id": "05kq2htc"
	}


Available Implementations
=========================

Open source libraries implementing some or all of the functionality described
in this document are available for the following programming languages:

- [Java](https://github.com/ninchat/ninchat-java) -
  [Javadoc](https://ninchat.github.io/ninchat-java/master)
- [Node.js](https://github.com/ninchat/ninchat-nodejs)
- [PHP](https://github.com/ninchat/ninchat-php)
- [Python](https://github.com/ninchat/ninchat-python) -
  [read the docs](https://ninchat-python.readthedocs.org/en/latest/master.html)

