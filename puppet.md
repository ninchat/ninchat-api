Ninchat Puppets
===============

Copyright &copy; 2017 Somia Reality Oy.  All rights reserved.


### Contents

- [Introduction](#introduction)
- [Creating Puppets](#creating-puppets)
- [Puppet Login](#puppet-login)
- [Puppet Control](#puppet-control)
- [Puppet Attributes](#puppet-attributes)


### Associated documents

- [Ninchat Master Keys](master.md)
- [Ninchat API Reference](api.md)


Introduction
------------

A Ninchat user account may optionally be:

- Master of other users.  A master owns its puppets in the sense that it has
  complete control over them.
- Puppet of another user.  A user may have only one master.

In other words, a group of users forms a tree structure, rooted at a master
user.

Puppet users are intended to be used when integrating a third-party service's
end user accounts with Ninchat: there should be a puppet for each end user who
needs to be able to communicate via Ninchat.  The primary benefit of puppets is
that they don't need to have individual authentication tokens--after all, the
third-party service already takes care of end user authentication.

There are no restrictions on master nor puppet users; they may be used like any
normal user.


Creating Puppets
----------------

Currently the only way to create a master-puppet relationship is for the master
user to create a puppet user.  There are two mechanisms:

- Calling the [`create_user`](api.md#create_user) API action.  The caller will
  become the master of the new user.
- Creating an [action signature](master.md#action-signatures) for
  [`create_session`](api.md#create_session) (the variant which creates new
  users), and passing it to a client which invokes the API action.  The owner
  of the signing key will become the master of the new user.


Puppet Login
------------

When an end user needs to be logged in for an interactive session, an [action
signature](master.md#action-signatures) is created for
[`create_session`](api.md#create_session) (the variant which logs in existing
users), and passed to the client which invokes the API action.


Puppet Control
--------------

Most API actions support the `puppet_id` parameter.  It allows a master to
impersonate one of its puppets while invoking an action.  (This is somewhat
analoguous to `sudo -u` in Unix.)

The puppet's privileges will be applied when processing the action; if the
master wishes the puppet to gain access to the master's resources, that needs
to be authorized by simultaneously specifying an [action
signature](master.md#action-signatures).


Puppet Attributes
-----------------

Puppet users may control themselves like any normal user, including modifying
user attributes.  A master may enforce [separate attributes](api.md#puppet) on
its puppets, which the puppet users themselves cannot override.

A puppet's attributes are visible to other members of realms and channels which
are owned by the puppet's master.  Client implementations will see both user
and puppet attributes, and are responsible for consolidating the information.
