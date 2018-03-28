Ninchat Master Keys
===================

This document describes Ninchat master keys (API keys).

Copyright &copy; 2015 Somia Reality Oy.  All rights reserved.


### Contents

- [Key Types](#key-types)
- [Creating Keys](#creating-keys)
- [Single Sign-On](#single-sign-on)
- [Secure Metadata](#secure-metadata)


### Associated documents

- [Ninchat Signing and Secure Metadata](master/ninchat.md)
- [Using JWT with Ninchat Master Keys](master/jwt.md)
- [Ninchat Puppets](puppet.md)
- [Ninchat API Reference](api.md)


Key Types
---------

A master key always ultimately belongs to a specific Ninchat user.  When the
key is used, that *master user* exerts control over other users or resources.

Ninchat supports two types of master keys: "ninchat"-type keys are used with
the algorithms described in
[Ninchat Signing and Secure Metadata](master/ninchat.md), and "jwt"-type keys
are used for creating JWT tokens; see
[Using JWT with Ninchat Master Keys](master/jwt.md).


Creating Keys
-------------

API keys can be created in two ways:

- Using the https://ninchat.com/app/#/x/settings/masterkeys user interface.
- Using the [`create_master_key`](api.md#create_master_key) API action.

By default a master key may be used for the following things:

- Authentication and control of puppet users.
- Authorizing access to the master user's resources (such as channels).

A master key may optionally be specific to a realm (aka. organization).  Such
keys differ from the non-specific ones in the following ways:

- They may not be used with puppets.
- They authorize access only to the specific realm's resources.
- Also the realm's operators may create and delete the keys.


Single Sign-On
--------------

Single sign-on can be implemented by generating
[session action signatures](master/ninchat.md#action-signatures) or
[JWT authentication tokens](master/jwt.md#authentication), and passing them to
Ninchat.


### Ninchat website

An existing puppet user can be logged in at the Ninchat website by forming an
URL:

	https://ninchat.com/app/#/x/login-sign/USER_ID/MASTER_KEY_TYPE/MASTER_SIGN

- `USER_ID` is the Ninchat user id to log in.
- `MASTER_KEY_TYPE` is "ninchat" (JWT is not supported yet).
- `MASTER_SIGN` is the generated signature.


### Embedded Ninchat

A third-party service's user can be logged in via the embedded Ninchat client
by specifying the `masterKeyType` and `masterUserSign` parameters.  If the key
type is "ninchat" and an existing user is to be logged in, the `userId`
parameter must also be specified.  Ninchat user id is never needed if the key
type is "jwt".

If the user needs to be added to a channel, also the `masterChannelSign`
parameter needs to be specified.  A single JWT token containing authentication
and authorization claims can be used as both the user and the channel
signature.  But if the key type is "ninchat", a separate channel action
signature needs to be generated.


Secure Metadata
---------------

When Ninchat is integrated to a third-party service, secure metadata can be
used to communicate arbitrary end user related information to the customer care
agent.  It typically contains identification of an authenticated user, plus
other information that is helpful for the agent during the chat.

Secure metadata is encrypted by the third-party server, using the
[original encoding](master/ninchat.md#secure-metadata) or encapsulated in a
[JWT token](master/jwt.md#secure-metadata).  The encrypted string is then
passed to the web browser on the page which embeds Ninchat.

Non-secure metadata is specified via the embedded Ninchat client's
`audienceMetadata` parameter, and secure metadata is included in the "secure"
property.

