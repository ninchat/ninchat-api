Ninchat Master Keys
===================

This document describes Ninchat master keys (API keys).

Copyright &copy; 2015 Somia Reality Oy.  All rights reserved.


### Contents

- [Key Types](#key-types)
- [Creating Keys](#creating-keys)


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

