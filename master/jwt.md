Using JWT with Ninchat Master Keys
==================================

JSON Web Tokens are specified in IETF RFCs
[7515](https://tools.ietf.org/html/rfc7515) (JWS),
[7516](https://tools.ietf.org/html/rfc7516) (JWE) and
[7519](https://tools.ietf.org/html/rfc7519) (JWT).  Additional resources (such
as information about programming language support) can be found at
[jwt.io](https://jwt.io).  This document explains how JWT fits into the Ninchat
API.

Copyright &copy; 2018 Somia Reality Oy.  All rights reserved.


### Contents

- [Common specifications](#common-specifications)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [Secure Metadata](#secure-metadata)


### Associated documents

- [Ninchat Master Keys](../master.md)
- [Ninchat Signing and Secure Metadata](ninchat.md)
- [Ninchat Puppets](../puppet.md)
- [Ninchat API Reference](../api.md)


Common specifications
---------------------

### Header parameters

Tokens must be signed or encrypted using a master key.  The master key id must
be specified via the standard `kid` header parameter.

Supported algorithms:

- HS256 for signing, specified via the `alg` header parameter.
- A256GCM for encryption, specified via the `enc` header parameter, with `alg`
  set to "dir".

Arbitrary algorithms are not allowed for security reasons.


### Claims

Expiration time must be specified via the standard `exp` claim in the payload.
The tokens must expire within one week (preferably a lot sooner).


Authentication
--------------

The [`create_session`](../api.md#create_session) API action supports logging in
puppet users using JWT tokens created by their master user.  The token is
passed via the `master_sign` parameter, with `master_key_type` as "jwt".

The standard `sub` (subject) claim is required.  It should be an arbitrary but
unique user identifier string.  The first time when Ninchat sees a given
subject id, it creates a new user.

The `preferred_username` claim can optionally be used to set the
[puppet name attribute](../api.md#puppet).  The end user cannot change or unset
it through Ninchat; it is controlled completely by the master user.  (The claim
name has been borrowed from
[OpenID Connect](https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims).)


Authorization
-------------

The [`follow_channel`](../api.md#follow_channel) and
[`join_channel`](../api.md#join_channel) API actions support JWT tokens for
granting access to a master user's non-public channels.  The token is passed
via the `master_sign` parameter, with `master_key_type` as "jwt".

The `scopes` claim is a string array which should contain the scope string of
the target channel.  The scope string format is "channel:*ID*", where *ID* is
the channel id.  (The target channel's id must also be specified in the API
action's `channel_id` parameter even if there is only one scope listed in the
JWT token.)


Secure Metadata
---------------

The [`request_audience`](../api.md#request_audience) API action supports
JWT-encapsulated metadata as an alternative for the
[original encoding](ninchat.md#secure-metadata).  It is specified in the
"secure" property in an object passed to the `audience_metadata` parameter.
(Ninchat detects the master key type automatically.)

The `ninchat.com/metadata` claim is an object containing the secure metadata.

The token must be encrypted; the JWT must be a JWE, not a JWS.

See [Python example code](../examples/jwt_secure_metadata.py).


Notes
-----

JWT libraries have different feature sets and APIs.  Many libraries don't
support encryption, so they cannot be used for secure metadata.

Ninchat master key is provided in base64-encoded form.  JWT libraries differ in
the way they expect the key material to be specified: some expect a
base64-encoded key, others expect a raw binary key.  If a library doesn't
expect a base64-encoded key, the secret key must be decoded first.

