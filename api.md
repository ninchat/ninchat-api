Ninchat API Reference
=====================

This document describes version 2 of the open [Ninchat](https://ninchat.com)
API.  It will be extended over time, without causing regressions to conforming
client applications.  If a new, backward-incompatible API version is released,
it will be accessible using new network endpoints.

Copyright &copy; 2012-2017 Somia Reality Oy.  All rights reserved.


### Contents

- [Changes](#changes)
- [Interface](#interface)
  - [Actions](#actions)
  - [Events](#events)
  - [Attributes](#attributes)
    - [Channel](#channel)
    - [Channel membership](#channel-membership)
    - [Dialogue membership](#dialogue-membership)
    - [File](#file)
    - [Identity](#identity)
    - [Puppet](#puppet)
    - [Queue](#queue)
    - [Realm](#realm)
    - [Realm membership](#realm-membership)
    - [Tag](#tag)
    - [User](#user)
  - [User settings](#user-settings)
  - [Error types](#error-types)
  - [Message types](#message-types)
    - [ninchat.com/file](#ninchatcomfile)
    - [ninchat.com/info/*](#ninchatcominfo)
    - [ninchat.com/link](#ninchatcomlink)
    - [ninchat.com/metadata](#ninchatcommetadata)
    - [ninchat.com/notice](#ninchatcomnotice)
    - [ninchat.com/text](#ninchatcomtext)
  - [Audience metadata](#audience-metadata)
- [Streaming Transports](#streaming-transports)
  - [WebSocket](#websocket)
  - [HTTP long polling](#http-long-polling)
- [Sessionless HTTP Calling](#sessionless-http-calling)
  - [Requests](#requests)
  - [Responses](#responses)


### Associated documents

- [Ninchat Master Keys](master.md)
  - [Action Signatures](master.md#action-signatures)
  - [Secure Metadata](master.md#secure-metadata)
- [Ninchat Puppets](puppet.md)


Changes
=======

### Version 2

Backward-incompatible changes from version 1:

- [WebSocket](#websocket) clients must be prepared to handle text and binary
  frames.  (Previously only text frames were sent to clients.)

- The initial value of the `action_id` parameter must be 1 (instead of any
  positive integer), and it must be reset to 1 when a new session is created
  and there are no action retries queued from previous sessions.  (See the
  [Interface](#interface) section.)

- The `ninchat.com/info` message type is split into multiple
  [`ninchat.com/info/*`](#ninchatcominfo) types.

- Message content must consist of at least one part.  (See the
  [`send_message`](#send_message) action.)

- The [`message_received`](#message_received) event might not include the
  message content.

- The `message_time` parameter type changed from integer to float.  (See the
  [`message_received`](#message_received) event.)

- The [`search_results`](#search_results) event's "users" and "channels"
  objects were modified to accommodate more parameters.

- The [`session_created`](#session_created) event might not include the
  `session_host` parameter.

- The WebSocket-Protocol header is now unversioned; the API version is included
  in the [WebSocket](#websocket) endpoint URL.

See the [commit log](https://github.com/ninchat/ninchat-api/commits/v2/api.md)
for incremental changes.


Interface
=========

Clients send actions to the server, which sends events to clients.  Action and
event parameter values are represented as JSON types.

Most actions support or require the `action_id` parameter, which may be used to
detect success or failure of the action.  The action reference indicates the
exceptions when it is *not* supported.  When the client receives (at least) one
event with the corresponding `action_id`, the action has succeeded, unless
the event was `error`.  The values should be ascending integers, starting at 1,
over the lifetime of the client instance's state (even across sessions).  If no
response event is received, the client may retry the action (e.g. after
reconnecting) with the same `action_id` value.

Most actions support the `puppet_id` parameter.  The action reference indicates
the exceptions when it is *not* supported.  See the
[Ninchat Puppets](puppet.md) document for more information.

In addition to the parameters listed below, most events contain the
monotonically ascending `event_id` integer parameter (starting at 1).  Such
events are buffered by the server until they are acknowledged by the client, so
that they can be retransmitted if the network connection is lost during a
session.  (Events without an `event_id` are connection-specific.)  The
acknowledgement procedure is transport-specific (see
[Streaming Transports](#streaming-transports)).  Failure to acknowledge events
results in session buffer overflow.

Instead of the reply events listed below, any action may cause an `error`
event.

Undefined action, event and parameter names must not be used in communication
and you should not rely on their nonexistence.  Enumerations
(e.g. `access_type`, `error_type` and `identity_type`) may gain new options, so
clients should be able to cope with events with unknown values for such
parameters.

When a newer API version is available, a client accessing an old API endpoint
may receive an unsolicited `error` event with error_type set to `deprecated`.
(It's purely informational, and doesn't necessarily imply immediate service
degradation.)


Actions
-------

### `create_session`

- `user_id` : string (optional)
- `user_auth` : string (optional)
- `user_attrs` : object (optional)
- `user_settings` : object (optional)
- `user_metadata` : object (optional)
- `identity_type` : string (optional)
- `identity_name` : string (optional)
- `identity_auth` : string (optional)
- `identity_type_new` : string (optional)
- `identity_name_new` : string (optional)
- `identity_auth_new` : string (optional)
- `identity_attrs` : object (optional)
- `access_key` : string (optional)
- `master_key_type` : string (optional)
- `master_sign` : string (optional)
- `puppet_attrs` : object (optional)
- `message_types` : string array

Exceptions:

- `puppet_id` is not supported.
- `session_id` is not supported (see [Streaming Transports](#streaming-transports)).

Reply event: [`session_created`](#session_created)

There are five modes of operation:

1. If `user_id` and `user_auth` are specified, a new session for an existing
   user is created.

2. If `identity_type`, `identity_name` and `identity_auth` are specified, a new
   session for an existing user is created.  The identity type and name must be
   verified for a user.

   If `identity_type` is set to "facebook", `identity_name` is set to a
   Facebook user id and `identity_auth` contains a matching signed request, a
   session is created for the existing Ninchat user with the associated
   Facebook identity.

3. If `access_key` is specified, a new session for an existing user is created.
   The access key configuration determines the user.

4. If `user_id` and `master_sign` are specified, a new session for an existing
   user is created.  `master_key_type` specifies the signature type (defaults
   to "ninchat").  An `access_expired` error type is returned if the signature
   has expired.  See [Action signatures](master.md#action-signatures).

5. Otherwise a new user is created.

   The user will be a guest unless the `guest` user attribute is explicitly set
   as false.

   `identity_type_new`, `identity_name_new`, `identity_auth_new` and/or
   `identity_attrs` may be used to create an identity for the user.

   If `identity_type_new` is set to "facebook", `identity_name_new` is set to a
   Facebook user id and `identity_auth_new` contains a matching signed request
   from the Facebook SDK, the Facebook identity is associated with the created
   Ninchat user.

Accepted message types are specified as a list of strings to compare against
incoming message types.  If a string ends with an asterisk (\*), the substring
preceding the asterisk is used to match prefixes instead of whole strings.  The
"*" string accepts all messages.  An empty array rejects all messages.

If the authentication token or access key is invalid or has been revoked, the
error type will be `access_denied`.  This condition is permanent:
`create_session` won't succeed later with the same parameters.


### `resume_session`

Exceptions:

- `puppet_id` is not supported

Receive or acknowledge events of an existing session.  See
[Streaming Transports](#streaming-transports) for details.


### `update_session`

- `session_idle` : boolean (optional)
- `channel_id` : string (optional)
- `user_id` : string (optional)
- `message_id` : string (optional)

Exceptions:

- `puppet_id` is not supported.

Client-assisted idle user and unread message tracking.


### `close_session`

Exceptions:

- `puppet_id` is not supported.

See [Streaming Transports](#streaming-transports) for details.


### `create_user`

- `action_id` : integer
- `user_attrs` : string (optional)
- `user_settings` : string (optional)
- `puppet_attrs` : object (optional)

Reply event: [`user_created`](#user_created)

Like [`create_session`](#create_session), but doesn't create a session.  Useful
with the [sessionless API](#sessionless-http-calling).

If called by an existing user (e.g. there is a session, or the caller is
authenticated), the created user will become a puppet of the calling (master)
user.  The [`user_created`](#user_created) event won't include the `user_auth`
parameter; instead, the puppet user may be logged in and manipulated using the
master key mechanism.

If called without a session or authentication credentials, a standalone user is
created.  The [`user_created`](#user_created) event will include the
`user_auth` parameter.

The created user will be a guest unless the `guest` user attribute is
explicitly set as false.


### `describe_user`

- `action_id` : integer
- `user_id` : string (optional)

Reply event: [`user_found`](#user_found)


### `update_user`

- `action_id` : integer
- `user_attrs` : object (optional)
- `user_settings` : object (optional)
- `payload_attrs` : string array (optional)

Reply event: [`user_updated`](#user_updated)

The `iconurl` attribute may be set by uploading image data in the payload: the
index of the payload frame is determined by the index of the "icon" string in
the `payload_attrs` array.  WebSocket example:

First frame:

	{
	  "action":        "update_user",
	  "action_id":     3,
	  "payload_attrs": ["icon"],
	  "frames":        1
	}

Second frame:

	\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x03
	\x00\x00\x00%\xdbV\xca\x00\x00\x00\x03PLTE\x93c+\xbaC\xfaW\x00\x00\x00\nIDA
	T\x08\xd7c`\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82


### `delete_user`

- `action_id` : integer
- `user_auth` : string (optional)

Reply event: [`user_deleted`](#user_deleted)

The `user_auth` token must be repeated here to avoid accidents and mischief,
except for guest users, or when this action is invoked with `puppet_id`.


### `create_identity`

- `action_id` : integer
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object (optional)
- `identity_auth_new` : string (optional)

Reply event: [`identity_created`](#identity_created)

Associates an identity with the session user.  The identity is pending
verification until futher action is taken.

Identity types:

- "email" sends an email with a verification link.  `identity_name` specifies
  the email address.
- "facebook" creates an identity to be used for authentication with the help of
  the Facebook SDK.  See `create_session`.
- "gcm" registers a GCM id.  `identity_name` specifies the GCM registration id.
- "apns" registers an APNs id.  `identity_name` specifies the APNs device id.

A secret authentication token (password) is associated with the identity if
`identity_auth_new` is specified.


### `create_identity_with_auth_reset_access`

- `action_id` : integer
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object (optional)

Reply event: [`identity_created`](#identity_created)

Combines the [`create_identity`](#create_identity) and
[`request_identity_auth_reset_access`](#request_identity_auth_reset_access)
actions: password is not set by the action, but via a link received in an
email.  The identity will be verified when a password is set (via the link).


### `request_identity_verify_access`

- `action_id` : integer (optional)
- `identity_type` : string
- `identity_name` : string

Exceptions:

- `session_id` is optional (see [Streaming Transports](#streaming-transports)).

Reply event: `access_created` (without `access_key`)

Resend an email identity verification link if the identity is still pending
verification.  (In other words, `identity_type` must be "email" for now.)


### `verify_identity`

- `action_id` : integer (optional)
- `access_key` : string
- `identity_accept` : boolean

Exceptions:

- `session_id` is optional (see [Streaming Transports](#streaming-transports)).

Reply event: [`identity_updated`](#identity_updated)

Accepts or rejects a pending user identity.


### `describe_identity`

- `action_id` : integer
- `identity_type` : string
- `identity_name` : string

Reply event: [`identity_found`](#identity_found)


### `update_identity`

- `action_id` : integer
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object

Reply event: [`identity_updated`](#identity_updated)


### `update_identity_auth`

- `action_id` : integer
- `identity_type` : string
- `identity_name` : string
- `identity_auth` : string (optional)
- `identity_auth_new` : string (optional)

Reply event: [`identity_updated`](#identity_updated)

Sets or changes the secret authentication token (password).

`identity_auth` (the old authentication token) must be specified if the
identity already has one.  It will be replaced with `identity_auth_new`.  If
`identity_auth_new` is not specified, the password will be removed.


### `request_identity_auth_reset_access`

- `action_id` : integer (optional)
- `identity_type` : string
- `identity_name` : string

Exceptions:

- `session_id` is optional (see [Streaming Transports](#streaming-transports)).

Reply event: [`access_created`](#access_created) (without `access_key`)

Create and send an access key to the specified email address if it's a verified
email identity.  (In other words, `identity_type` must be "email" for now.)
The access key may be used to reset the password associated with the identity.


### `reset_identity_auth`

- `access_key` : string
- `identity_auth_new` : string

Exceptions:

- `session_id` is optional (see [Streaming Transports](#streaming-transports)).

Reply event: [`identity_updated`](#identity_updated)

Resets the authentication token (password) associated with an identity
(specified by the `access_key`).


### `delete_identity`

- `action_id` : integer
- `identity_type` : string
- `identity_name` : string
- `identity_auth` : string (optional)

Reply event: [`identity_deleted`](#identity_deleted)

`identity_auth` must be specified if the identity has one.


### `update_dialogue`

- `action_id` : integer
- `user_id` : string
- `member_attrs` : object (optional)
- `dialogue_status` : string (optional)

Reply event: [`dialogue_updated`](#dialogue_updated)

Update your own member attributes in your dialogue with `user_id`, or your
perceived status of the dialogue.  Valid values for `dialogue_status` are
"visible" (not hidden, not highlighted) and "hidden".


### `create_channel`

- `action_id` : integer
- `channel_attrs` : object (optional)
- `realm_id` : string (optional)

Reply event: [`channel_joined`](#channel_joined)

If `realm_id` is specified, the realm owner will become the channel owner.
Otherwise the session user will become the owner.


### `describe_channel`

- `action_id` : integer
- `channel_id` : string

Reply event: [`channel_found`](#channel_found)


### `update_channel`

- `action_id` : integer
- `channel_id` : string
- `channel_attrs` : object

Reply event: [`channel_updated`](#channel_updated)


### `follow_channel`

- `action_id` : integer
- `channel_id` : string
- `master_key_type` : string (optional)
- `master_sign` : string (optional)

Reply event: [`channel_found`](#channel_found)

Like [`join_channel`](#join_channel), but:

- May only be used with channels with the `disclosed_since` and `followable`
  attributes set, and without the `private` attribute set.  Note: channels in
  realms may be followable even when the `public` attribute is not set!
- The user won't appear on the channel's member list.
- The user won't be able to send messages to the channel.
- Only the session which invoked this action will receive `message_received`
  events for this channel.
- The user will stop following the channel when the session is closed.


### `join_channel`

- `action_id` : integer
- `channel_id` : string (optional)
- `access_key` : string (optional)
- `master_key_type` : string (optional)
- `master_sign` : string (optional)
- `member_attrs` : object (optional)

Reply events: [`channel_joined`](#channel_joined) and
              [`realm_joined`](#realm_joined) (if applicable)

There are three modes of operation:

1. `channel_id` specifies the channel to be joined.  It must not be in a realm
   or it must be in one of the user's realms.

2. `access_key` grants permission to join a channel in a realm.  The access key
   configuration determines the channel to be joined.  The
   [`realm_joined`](#realm_joined) event indicates that the user was granted
   access to the channel's realm in addition to the channel (depending on the
   access key configuration).

3. `master_sign` grants permission to join the channel.  `master_key_type`
   specifies the signature type (defaults to "ninchat").  See
   [Action signatures](master.md#action-signatures).

`member_attrs` can only be specified in conjunction with `master_sign`, when
`master_key_type` is "ninchat" (see [Ninchat Master Keys](master.md)).  It can
only be used to disable the "silenced" member attribute, when the channel has
"autosilence" attribute enabled.


### `part_channel`

- `action_id` : integer
- `channel_id` : string

Reply event: [`channel_parted`](#channel_parted)


### `create_realm`

- `action_id` : integer
- `realm_attrs` : object (optional)
- `realm_settings` : object (optional)
- `channel_attrs` : object (optional)

Reply events: [`realm_joined`](#realm_joined) and
              [`channel_joined`](#channel_joined) (if applicable)

Creates a realm, and an optional initial channel if `channel_attrs` is defined.
The session user will become the owner of both.


### `describe_realm`

- `action_id` : integer
- `realm_id` : string

Reply event: [`realm_found`](#realm_found)


### `describe_realm_queues`

- `action_id` : integer
- `realm_id` : string
- `queue_ids` : string array (optional)
- `track_stage` : string (optional)
- `track_metadata` : object (optional)

Reply event: [`realm_queues_found`](#realm_queues_found)

Describe some or all audience queues of a realm.

If specified, `queue_ids` indicates a subset of the realm's queues which the
user is interested in.  Unknown queue ids are silently ignored.  (The user may
still receive spurious `queue_updated` events concerning the realm's other
queues.)


### `update_realm`

- `action_id` : integer
- `realm_id` : string
- `realm_attrs` : object (optional)
- `realm_settings` : object (optional)

Reply event: [`realm_updated`](#realm_updated)


### `delete_realm`

- `action_id` : integer
- `realm_id` : string

Reply event: [`realm_deleted`](#realm_deleted)


### `create_queue`

- `action_id` : integer
- `realm_id` : string
- `queue_attrs` : object

Reply event: [`queue_created`](#queue_created)

Create a new audience queue.  Caller must be a realm operator.


### `update_queue`

- `action_id` : integer
- `queue_id` : string
- `queue_attrs` : object (optional)
- `queue_settings` : object (optional)

Reply event: [`queue_updated`](#queue_updated)

Update audience queue attributes and/or settings.  Caller must be a realm
operator.


### `delete_queue`

- `action_id` : integer
- `queue_id` : string

Reply event: [`queue_deleted`](#queue_deleted)

Delete an audience queue.  Caller must be a realm operator.


### `describe_queue`

- `action_id` : integer
- `queue_id` : string

Reply event: [`queue_found`](#queue_found)

Describe an audience queue.


### `request_audience`

- `action_id` : integer
- `queue_id` : string
- `audience_metadata` : object (optional)

Reply event: [`audience_enqueued`](#audience_enqueued)

Go to the end of the queue.

The `audience_metadata` object may contain arbitrary properties, but the
"secure" property is special: if set to a string value, it will be decrypted
using the queue owner's master key, and the contents will be set as the value
of the property.  Other value types for "secure" property are rejected.  A
`permission_expired` error type is returned if the encrypted metadata has
expired.  See [Secure metadata](master.md#secure-metadata).


### `accept_audience`

- `action_id` : integer
- `queue_id` : string

Reply event: [`dialogue_updated`](#dialogue_updated)

Take the first user from the queue.  Caller must be a queue member.  The
`queue_id` dialogue member attribute will be set for the accepted user.


### `add_member`

- `action_id` : integer
- `realm_id` : string (optional)
- `queue_id` : string (optional)
- `user_id` : string

Reply event: [`realm_member_joined`](#realm_member_joined) or [`queue_member_joined`](#queue_member_joined)

Causes a specific user to join a realm or an audience queue.  Caller must be a
realm opereator.


### `update_member`

- `action_id` : integer
- `channel_id` : string (optional)
- `realm_id` : string (optional)
- `user_id` : string
- `member_attrs` : object
- `interval_end` : float (optional)

Reply event: [`channel_member_updated`](#channel_member_updated) or
             [`realm_member_updated`](#realm_member_updated)

Sets or clears a channel or realm membership attributes for a user.

If `interval_end` is specified with a channel membership attribute, the set
attribute will be automatically unset at that time.  (An `update_member` call
with an interval can set only one attribute at a time.)


### `remove_member`

- `action_id` : integer
- `channel_id` : string (optional)
- `realm_id` : string (optional)
- `queue_id` : string (optional)
- `user_id` : string

Reply event: [`channel_member_parted`](#channel_member_parted),
             [`realm_member_parted`](#realm_member_parted) or
             [`queue_member_parted`](#queue_member_parted)

Kicks a user out of a channel, a realm or an audience queue.  Caller must be
the target user, a channel operator or moderator (if removing from a channel)
or a realm operator (if removing from a realm or a queue).


### `send_message`

- `action_id` : integer (optional)
- `channel_id` : string (optional)
- `user_id` : string (optional)
- `identity_type` : string (optional)
- `identity_name` : string (optional)
- `message_type` : string
- `message_recipient_ids` : string array (optional)
- `message_fold` : boolean (optional)
- `message_ttl` : float (optional)

Reply event: [`message_received`](#message_received) or none (if `action_id` is
             not specified)

Message content is provided in the payload (see
[Streaming Transports](#streaming-transports)).  The content may not be empty:
it must contain one or more parts (but the individual parts may be
zero-length).

Exactly one of `channel_id`, `user_id` and `identity_name` must be specified.
`user_id` specifies a private conversation party.  `identity_type` and
`identity_name` specify a private conversation party without an established
user account.

If `message_ttl` is specified, restrictions are placed on message delivery: the
message may not be stored in the channel/dialogue history and messages may be
dropped by unresponsive sessions.  `message_ttl` specifies the minimum time in
seconds to buffer the message (which should be the upper limit for the
usefulness of the content).  Sending such a message to an identity doesn't make
sense.


### `update_message`

- `action_id` : integer
- `channel_id` : string
- `message_id` : string
- `message_hidden` : boolean

Reply event: [`message_updated`](#message_updated)

Available for channel operators and moderators.  Affects a single message on
the channel.


### `update_user_messages`

- `action_id` : integer
- `channel_id` : string
- `message_user_id` : string
- `message_id` : string (optional)
- `interval_end` : float (optional)
- `message_hidden` : boolean

Reply event: [`message_updated`](#message_updated)

Available for channel operators and moderators.  Affects all messages up to and
including `message_id` which have been sent by `message_user_id` to the
channel.  `interval_end` may be used instead of `message_id` to specify the
(inclusive) end of time range.


### `load_history`

- `action_id` : integer
- `channel_id` : string (optional)
- `user_id` : string (optional)
- `message_types` : string array (optional)
- `message_id` : string (optional)
- `message_fold` : boolean (optional)
- `history_length` : integer (optional)
- `history_order` : integer (optional)
- `filter_property` : string
- `filter_substring` : string

Reply events: [`history_results`](#history_results) and
              [`message_received`](#message_received) multiple times (with
              `history_length` set)

Exactly one of `channel_id` and `user_id` must be specified.  `user_id`
specifies a private conversation party.

`message_types` defaults to the value passed to `create_session`.

`message_id` makes it possible to fetch additional messages if you already have
some.  It specifies the exclusive first or last message identifier (depending
on the `history_order` parameter).  The latest messages are returned by
default.  Empty string indicates the beginning of history.

If `message_fold` is set, only folded messages are returned.

The meaning of `history_length` is as follows:

1. In the `load_history` action it specifies the number of requested messages.
2. In the `history_results` event it specifies the number of available
   messages.
3. In the `message_received` event it specifies the number of remaining
   messages.

`history_order` specifies the order in which the messages will be received.
When used in combination with `message_id`, its value also determines if we are
fetching older or newer messages:

- -1 requests newer messages first (descending).  `message_id` specifies the
  exclusive end of range.  This is the default.
- 1 requests older messages first (ascending).  `message_id` specifies the
  exclusive start of range.

If `filter_property` and `filter_substring` are specified, only messages which
contain the `filter_substring` in the value of their `filter_property` are
returned (if supported for the message type).  `message_types` should contain
only supported message types (see [Message Types](#message-types)); other
messages are ignored.  `history_length` specifies the number of returned
messages.


### `discard_history`

- `action_id` : integer (optional)
- `user_id` : string
- `message_id` : string

Reply event: [`history_discarded`](#history_discarded) (without
             `history_length` set) or none (if `action_id` is not specified)

`user_id` specifies a private conversation party.  `message_id` specifies the
latest message to be discarded.


### `create_access`

- `action_id` : integer
- `access_type` : string
- `channel_id` : string (optional)
- `channel_unsilence` : boolean (optional)
- `realm_member` : boolean (optional)
- `user_id` : string (optional)

Reply event: [`access_created`](#access_created)

Creates an access key for use with [`create_session`](#create_session) or
[`join_channel`](#join_channel).

Access types:

- "session" keys may be used in `create_session` actions.
- "channel" keys may be used in a single `join_channel` action.  If
  `channel_unsilence` is true, the invited user will not be silenced even if
  the channel has the `autosilence` attribute set.  If `realm_member` is true,
  the invited user will also join the realm of the channel (if any).  If
  `user_id` is specified, the invite can only be used by that user, and an info
  message is sent to that user (see [Message types](#message-types)).


### `send_access`

- `action_id` : integer
- `access_key` : string (optional)
- `user_id` : string (optional)
- `identity_type` : string (optional)
- `identity_name` : string (optional)

Reply event: [`access_found`](#access_found)

Send a pre-created channel access key to a user (= invite).  There are three
modes of operation:

1. If `access_key` and `user_id` are specified, a `ninchat.com/info/*` message
   is sent to the user in a dialogue.
2. If `access_key`, `identity_type` and `identity_name` are specified, an email
   is sent.  (In other words, `identity_type` must be "email" for now.)
3. If `identity_type` and `identity_name` are specified without `access_key`,
   the (undisclosed) access key associated with the user's identity is used, if
   any.  (This is the verification-link-resend feature.)


### `describe_access`

- `action_id` : integer (optional)
- `access_key` : string

Exceptions:

- `session_id` is optional (see [Streaming Transports](#streaming-transports)).

Reply event: [`access_found`](#access_found)


### `describe_master_keys`

- `action_id` : integer
- `realm_id` : string (optional)

Reply event: [`master_keys_found`](#master_keys_found)


### `describe_master` (deprecated)

- `action_id` : integer

Reply event: [`master_found`](#master_found)

This action has been superseded by
[`describe_master_keys`](#describe_master_keys).


### `create_master_key`

- `action_id` : integer
- `realm_id` : string (optional)
- `master_key_type` : string (optional)
- `master_key_id` : string (optional)

Reply event: [`master_key_created`](#master_key_created)

If `realm_id` is not specified, the created key can be used with any resource
owned by the creator (to the extent supported by the API).  In particular,
puppet users can be created and controlled with such keys.

If `realm_id` is specified, the created key can only be used with resources
associated with that realm (e.g. channels and audience metadata).  Such keys
can be created and deleted by realm operators.

If `master_key_type` is "ninchat" or left unspecified, an id and a secret key
are generated automatically.

If `master_key_type` is "jwt", `master_key_id` must be specified, and the key
material must be provided in the payload.


### `delete_master_key`

- `action_id` : integer
- `realm_id` : string (optional)
- `master_key_type` : string (optional)
- `master_key_id` : string
- `master_key_secret` : string (optional)
- `user_auth` : string (optional)

Reply event: [`master_key_deleted`](#master_key_deleted)

`realm_id` must be specified if the key is associated with a realm.

If the key is not associated with a realm (= it's a personal key), either
`master_key_secret` or `user_auth` must be specified for extra safety.

`master_key_type` defaults to "ninchat".


### `send_file`

- `action_id` : integer
- `file_attrs` : object
- `user_id` : string (optional)
- `channel_id` : string (optional)

Reply event: [`message_received`](#message_received)

File contents are uploaded in the first payload part.  A `ninchat.com/file`
message is sent to the specified user or channel.


### `describe_file`

- `action_id` : integer
- `file_id` : string

Reply event: [`file_found`](#file_found)


### `get_transcript`

- `action_id` : integer
- `channel_id` : string (optional)
- `dialogue_id` : string array (optional)
- `interval_begin` : float (optional)
- `interval_end` : float (optional)
- `message_id` : string (optional)

Reply event: [`transcript_contents`](#transcript_contents)

Dump the "ninchat.com/*" messages sent on a channel or in a dialogue.
`dialogue_id` holds a pair of user ids (the order doesn't matter).

Specifying a time interval may make sense when targetting a long-lived channel.
By default the interval is the whole history.

There is an unspecified technical limit on the number of messages returned at
once.  `message_id` may be used to get more messages if an earlier call didn't
return everything.


### `delete_transcript`

- `action_id` : integer
- `dialogue_id` : string array

Reply event: [`transcript_deleted`](#transcript_deleted)


### `describe_queue_transcripts`

- `action_id` : integer
- `queue_id` : string
- `interval_begin` : float
- `interval_end` : float (optional)
- `interval_ongoing` : boolean (optional)

Reply event: [`queue_transcripts_found`](#queue_transcripts_found)

List all dialogues which have started from the specified audience queue and
completed during the specified interval.  The interval may be open-ended, but
by default it will only return time slots which have already ended.  The
`interval_ongoing` parameter can be used to include unfinished transcripts of
the ongoing time slot.


### `delete_queue_transcripts`

- `action_id` : integer
- `queue_id` : string
- `interval_begin` : float
- `interval_end` : float

Reply event: [`queue_transcripts_deleted`](#queue_transcripts_deleted)

Discard all dialogues which have started from the specified audience queue and
completed during the specified interval.  The interval length must not exceed
one month.


### `create_tag`

- `action_id` : integer
- `realm_id` : string
- `tag_attrs` : object

Reply event: [`tag_created`](#tag_created)


### `describe_tag`

- `action_id` : integer
- `tag_id` : string

Reply event: [`tag_found`](#tag_found)


### `describe_tags`

- `action_id` : integer
- `realm_id` : string (optional)
- `tag_id` : string (optional)
- `tag_depth` : integer (optional)

Reply event: [`tags_found`](#tags_found)

Either `realm_id` or `tag_id` must be specified.  If `tag_depth` is specified,
it must be between 1 and 10 (inclusive).


### `update_tag`

- `action_id` : integer
- `tag_id` : string
- `tag_attrs` : object

Reply event: [`tag_updated`](#tag_updated)


### `delete_tag`

- `action_id` : integer
- `tag_id` : string

Reply event: [`tag_deleted`](#tag_deleted)


### `get_queue_stats`

- `action_id` : integer
- `queue_id` : string
- `stats_hour` : string (optional)
- `stats_length` : integer

Reply events: [`queue_stats_contents`](#queue_stats_contents)

`stats_hour` specifies the start of the time range as "YYYYMMDDHH"; if omitted,
the range ends at the latest occurrence of available data.  `stats_length`
specifies the number of hours to load.  No more than one month of data may be
requested at a time (does NOT need to be aligned to start or end of month).


### `search`

- `action_id` : integer
- `realm_id` : string (optional)
- `search_term` : string

Reply events: [`search_results`](#search_results) multiple times

Searches users and channels by name or realname prefixes.


### `search_users`

- `action_id` : integer
- `realm_id` : string (optional)
- `search_term` : string

Reply events: [`search_results`](#search_results) multiple times

Searches users by name or realname prefixes.


### `search_channels`

- `action_id` : integer
- `realm_id` : string (optional)
- `search_term` : string

Reply events: [`search_results`](#search_results) multiple times

Searches channels by name prefixes.


### `track`

- `action_id` : integer
- `realm_id` : string
- `queue_ids` : string array (optional)
- `track_stage` : string
- `track_metadata` : object

Reply event: [`ack`](#ack)


### `ping`

- `action_id` : integer (optional)

Reply events: [`pong`](#pong)


Events
------

### `error`

- `error_type` : string
- `error_reason` : string (optional)
- `session_id` : string (if applicable)
- `action_id` : integer (if applicable)
- `user_id` : string (if applicable)
- `identity_type` : string (if applicable)
- `identity_name` : string (if applicable)
- `channel_id` : string (if applicable)
- `realm_id` : string (if applicable)
- `queue_id` : string (if applicable)
- `tag_id` : string (if applicable)
- `message_type` : string (if applicable)


### `session_created`

- `session_id` : string
- `session_host` : string (optional)
- `user_id` : string
- `user_auth` : string (if a new authentication token was created)
- `user_attrs` : object
- `user_settings` : object
- `user_account` : object
- `user_identities` : object
- `user_dialogues` : object
- `user_channels` : object
- `user_realms` : object
- `user_realms_member` : object (optional)
- `user_queues` : object (optional)
- `puppet_masters` : object (optional)

If specified, `session_host` contains a hostname which should be used in
subsequent connections for this session.

If a new user was created, then `user_auth` contains a generated password which
may be used in future [`create_session`](#create_session) actions by the
client.

The `user_account` object contains information about channel, realm, queue and
file upload quota and service subscription (optional):

	"user_account": {
		"channels": {
			"quota":             10,
			"available":         3
		},
		"realms": {
			"quota":             3,
			"available":         2
		},
		"queues": {
			"quota":             5,
			"available":         4
		},
		"queue_members": {
			"quota":             5
		},
		"uploads": {
			"quota":             1073741824,
			"available":         917187592
		},
		"subscriptions": [
			{
				"active":        true,
				"plan":          "medium_free",
				"expiration":    1351776933
			},
			{
				"plan":          "small",
				"renewal":       1362888044,
				"channels": {
					"quota":     5,
					"suspended": 2
				},
				"realms": {
					"quota":     1,
					"suspended": 0
				},
				"queues": {
					"quota":     0,
					"suspended": 1
				},
				"queue_members": {
					"quota":     0
				},
				"uploads": {
					"quota":     1048576
				}
			}
		]
	}

The `user_identities` object consists of identity types mapped to objects
containing identity names mapped to identity attributes:

	"user_identities": {
		"email": {
			"user@example.com": { "attr": "value", ... },
			...
		},
		...
	}

The `user_dialogues` object consists of user identifiers (of users with whom
there are ongoing private conversations) mapped to objects containing the
optional `dialogue_members` object, `dialogue_status` string and
`audience_metadata` object:

	"user_dialogues": {
		"12345": {
			"dialogue_members": {
				"23456": { "attr": "value", ... },
				"65432": { "attr": "value", ... }
			},
			"dialogue_status": "highlight",
			"audience_metadata": { "attr": "value", ... }
		},
		...
	}

The `user_channels` object consists of channel identifiers mapped to objects
containing the `channel_attrs` object and the optional `channel_status` and
`realm_id` strings:

	"user_channels": {
		"12345": {
			"channel_attrs":  { "attr": "value", ... },
			"channel_status": "unread",
			"realm_id":       "67890"
		},
		...
	}

The `user_realms` object consists of realm identifiers mapped to objects
containing realm attributes:

	"user_realms": {
		"12345": { "attr": "value", ... },
		...
	}

The `user_realms_member` object consists of realm identifiers mapped to
objects containing the session user's realm membership attributes (if any):

	"user_realms_member": {
		"12345": { "operator": true, ... },
		...
	}

The `user_queues` object consists of queue identifiers mapped to objects
containing the `queue_attrs` object and the `realm_id` string.

	"user_queues": {
		"12345": {
			"queue_attrs": { "attr": "value", ... },
			"realm_id":    "67890"
		},
		...
	}

The `puppet_masters` object consists of master user identifiers mapped to
objects containing the `puppet_attrs` object:

	"puppet_masters": {
		"12345": {
			"puppet_attrs": { "attr": "value", ... }
		},
		...
	}


### `session_status_updated`

- `channel_id` : string (if applicable)
- `user_id` : string (if applicable)
- `message_id` : string

Another session indicated that it has read channel or dialogue messages up to
the specified message.


### `user_created`

- `action_id` : integer (if applicable)
- `user_id` : string
- `user_auth` : string (if a standalone user was created)
- `user_attrs` : object
- `user_settings` : object
- `puppet_masters` : object (optional)


### `user_found`

- `action_id` : integer (if applicable)
- `user_id` : string
- `user_attrs` : object
- `user_settings` : object (if the user is the session user)
- `user_account` : object (if the user is the session user)
- `user_identities` : object
- `user_dialogues` : object (if the user is the session user)
- `user_channels` : object (if the user is the session user)
- `user_realms` : object (if the user is the session user)
- `user_realms_member` : object (optional)
- `user_queues` : object (if the user is the session user)
- `dialogue_members` : object (if the session user has a dialogue with the user)
- `dialogue_status` : string (if the session user has a dialogue with the user
                              and there are unread messages)
- `message_time` : float (if the session user has a dialogue with the user)
- `audience_metadata` : object (if the session user has accepted an audience from the user)
- `puppet_masters` : object (optional)

The `dialogue_members` object consists of two user identifiers mapped to
dialogue membership attributes:

	"dialogue_members": {
		"12345": { "attr": "value", ... },
		"54321": { "attr": "value", ... }
	}

The dialogue membership attributes objects will be empty unless the user is the
session user.

If set, the value of `dialogue_status` will be "highlight", "unread" or
"hidden".  The `message_time` is the time of the latest message between the
users.


### `user_updated`

- `action_id` : integer (if applicable)
- `user_id` : string
- `user_attrs` : object
- `user_settings` : object (if the user is the session user)
- `user_account` : object (if the user is the session user)
- `puppet_masters` : object (optional)


### `user_deleted`

- `action_id` : integer (if applicable)
- `user_id` : string


### `identity_found`

- `action_id` : integer (if applicable)
- `user_id` : string
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object (if belonging to the session user)


### `identity_created`

- `action_id` : integer (if applicable)
- `user_id` : string
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object


### `identity_updated`

- `action_id` : integer (if applicable)
- `user_id` : string
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object


### `identity_deleted`

- `action_id` : integer (if applicable)
- `user_id` : string
- `identity_type` : string
- `identity_name` : string


### `dialogue_updated`

- `action_id` : integer (if applicable)
- `user_id` : string
- `dialogue_members` : object
- `dialogue_status` : string (if applicable)
- `message_time` : float (if applicable)
- `audience_metadata` : object (if the session user has accepted an audience from the user)
- `dialogue_metadata` : object (if the session user has accepted an audience from the user)


### `channel_found`

- `action_id` : integer (if applicable)
- `channel_id` : string
- `channel_attrs` : object
- `channel_members` : object (if the session user is a member)
- `channel_status` : string (if the session user is a member and there are
                             unread messages)
- `message_time` : float (if applicable)
- `realm_id` : string (if applicable)

The `channel_members` object consists of user identifiers mapped to objects
containing the `user_attrs` object, the `member_attrs` object (the
channel-specific attributes of the user) and the optional `puppet_attrs` object
(if the channel owner is a puppet master):

	"channel_members": {
		"12345": {
			"user_attrs": { "attr": "value", ... },
			"member_attrs": { "attr": "value", ... },
			"puppet_attrs": { "attr": "value", ... }
		},
		...
	}

If set, the value of `channel_status` will be "unread" or "highlight".  The
`message_time` is the time of the latest message.


### `channel_joined`

- `action_id` : integer (if applicable)
- `channel_id` : string
- `channel_attrs` : object
- `channel_members` : object
- `message_time` : float (if applicable)
- `realm_id` : string (if applicable)

The session user created a new or joined an existing channel.


### `channel_parted`

- `action_id` : integer (if applicable)
- `event_cause` : string (optional)
- `channel_id` : string

The session user left or was removed from a channel.


### `channel_updated`

- `action_id` : integer (if applicable)
- `event_cause` : string (optional)
- `channel_id` : string
- `channel_attrs` : object
- `realm_id` : string (if applicable)


### `channel_deleted`

- `action_id` : integer (if applicable)
- `channel_id` : string


### `channel_member_joined`

- `channel_id` : string
- `user_id` : string
- `user_attrs` : object
- `member_attrs` : object
- `puppet_attrs` : object (optional)

Someone else joined a channel.


### `channel_member_parted`

- `action_id` : integer (if applicable)
- `event_cause` : string (optional)
- `channel_id` : string
- `user_id` : string

Someone else left or was removed from a channel.

The `event_cause` is "member_remove" if the event was caused by a
`remove_member` action.


### `channel_member_updated`

- `action_id` : integer (if applicable)
- `channel_id` : string
- `user_id` : string
- `member_attrs` : object


### `realm_found`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `realm_attrs` : object
- `realm_settings` : object
- `realm_members` : object (if the session user is a member)

`realm_members` is analogous to [`channel_members`](#channel_found) described
above.


### `realm_queues_found`

- `action_id` : integer
- `realm_id` : string
- `realm_queues` : object

The `realm_queues` object consists of queue identifiers mapped to objects
containing `queue_attrs` (object) and optionally `queue_position` (integer):

	"realm_queues": {
		"12345": {
			"queue_attrs": {
				"name": "First World Problems",
				"length": 3
			},
			"queue_position": 1
		},
		...
	}


### `realm_joined`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `realm_attrs` : object
- `realm_settings` : object
- `realm_members` : object

The session user created a new or joined an existing realm.


### `realm_parted`

- `action_id` : integer (if applicable)
- `event_cause` : string (optional)
- `realm_id` : string

The session user left or was removed from a realm.


### `realm_updated`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `realm_attrs` : object
- `realm_settings` : object


### `realm_deleted`

- `action_id` : integer (if applicable)
- `realm_id` : string


### `realm_member_joined`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `user_id` : string
- `user_attrs` : object
- `member_attrs` : object
- `puppet_attrs` : object (optional)

Someone else joined a realm.


### `realm_member_parted`

- `action_id` : integer (if applicable)
- `event_cause` : string (optional)
- `realm_id` : string
- `user_id` : string

Someone else left or was removed from a realm.

The `event_cause` is "member_remove" if the event was caused by a
`remove_member` action.


### `realm_member_updated`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `user_id` : string
- `member_attrs` : object


### `queue_created`

- `action_id` : integer (if applicable)
- `queue_id` : string
- `queue_attrs` : object
- `queue_settings` : object
- `realm_id` : string (if applicable)


### `queue_found`

- `action_id` : integer (if applicable)
- `queue_id` : string
- `queue_attrs` : object
- `queue_settings` : object
- `queue_members` : object (if applicable)
- `queue_position` : integer (if applicable)
- `realm_id` : string (if applicable)

`queue_members` is analogous to `channel_members` (see the `channel_found`
event).


### `queue_updated`

- `action_id` : integer (if applicable)
- `event_cause` : string (optional)
- `queue_id` : string
- `queue_attrs` : object
- `queue_settings` : object
- `queue_position` : integer (if applicable)
- `realm_id` : string (if applicable)

`queue_position` is defined if you are currently in the queue.


### `queue_deleted`

- `action_id` : integer (if applicable)
- `queue_id` : string
- `realm_id` : string (if applicable)


### `queue_joined`

- `queue_id` : string
- `queue_attrs` : object
- `queue_settings` : object
- `realm_id` : string (if applicable)

You were added to an audience queue.


### `queue_parted`

- `event_cause` : string (optional)
- `queue_id` : string
- `realm_id` : string (if applicable)

You were removed from an audience queue.


### `queue_member_joined`

- `action_id` : integer (if applicable)
- `queue_id` : string
- `user_id` : string
- `user_attrs` : object
- `member_attrs` : object

Someone was added to an audience queue.


### `queue_member_parted`

- `action_id` : integer (if applicable)
- `event_cause` : string (optional)
- `queue_id` : string
- `user_id` : string

Someone was removed from an audience queue.

The `event_cause` is "member_remove" if the event was caused by a
`remove_member` action.


### `audience_enqueued`

- `action_id` : integer (if applicable)
- `queue_id` : string
- `queue_attrs` : object
- `queue_position` : integer


### `message_received`

- `action_id` : integer (if applicable)
- `channel_id` : string (if applicable)
- `user_id` : string (if applicable)
- `message_id` : string
- `message_time` : float
- `message_type` : string
- `message_user_id` : string (if applicable)
- `message_user_name` : string (if applicable)
- `message_recipient_ids` : string array (optional)
- `message_hidden` : boolean (optional)
- `message_fold` : boolean (optional)
- `message_ttl` : float (optional)
- `history_length` : integer (if succeeding a `history_results` event)

Message content is optionally provided in the payload (see
[Streaming Transports](#streaming-transports)).  The content may be omitted in
some cases, including but not limited to the situation when the sender session
hasn't subscribed to the sent message type, but expects a reply event.

`message_user_id` and `message_user_name` are not set for system messages (see
[Message types](#message-types)).


### `message_updated`

- `action_id` : integer (if applicable)
- `channel_id` : string (if applicable)
- `message_id` : string
- `message_hidden` : boolean (if applicable)


### `history_results`

- `action_id` : integer
- `channel_id` : string (if applicable)
- `user_id` : string (if applicable)
- `history_length` : integer
- `message_id` : string (if applicable)

The `message_id` is set to the last message's id if `history_length` > 0.  The
`history_order` specified in the `load_history` action causes this event's
`message_id` to be either the smallest or the greatest of the received ids.


### `history_discarded`

- `action_id` : integer
- `channel_id` : string (if applicable)
- `user_id` : string (if applicable)
- `message_id` : string


### `access_found`

- `action_id` : integer (if applicable)
- `access_type` : string
- `user_id` : string (if applicable)
- `user_attrs` : object (if applicable)
- `identity_type` : string (if applicable)
- `identity_name` : string (if applicable)
- `channel_id` : string (if applicable)
- `channel_attrs` : object (if applicable)
- `channel_unsilence` : boolean (if applicable)
- `realm_id` : string (if applicable)
- `realm_attrs` : object (if applicable)
- `realm_member` : boolean (if applicable)

The value of `access_type` is "session", "channel", "identity\_verify" or
"identity\_auth\_reset".  The relevant user, identity, channel and/or realm
properties are set:

- "session" access: `user_id` and `user_attrs` (the session user)
- "channel" access: `user_id`, `user_attrs` (the invitor), `channel_id`,
  `channel_attrs` (the target channel), `realm_id`, `realm_attrs` (if the
  target channel is in a realm) and `realm_member` (if the access key grants
  membership to the target channel's realm).
- "identity\_verify" and "identity\_auth\_reset" access: `user_id`,
  `user_attrs` (the identified user), `identity_type` and `identity_name` (the
  target identity)

(Generally speaking, the user properties describe the access key creator.)


### `access_created`

- `action_id` : integer (if applicable)
- `access_type` : string
- `access_key` : string (if applicable)


### `master_keys_found`

- `action_id` : integer
- `master_keys` : object

The `master_keys` object contains key types mapped to objects containing key
ids mapped to objects containing the optional `realm_id` property:

	"master_keys": {
		"ninchat": {
			"12345": {
			},
			"23456": {
				"realm_id": "01234"
			}
		}
		...
	}


### `master_found` (deprecated)

- `action_id` : integer
- `master_keys` : object

The `master_keys` object contains key ids mapped to empty objects:

	"master_keys": {
		"12345": {},
		...
	}


### `master_key_created`

- `action_id` : integer (optional)
- `realm_id` : string (optional)
- `master_key_type` : string
- `master_key_id` : string
- `master_key_secret` : string (optional)


### `master_key_deleted`

- `action_id` : integer (optional)
- `realm_id` : string (optional)
- `master_key_type` : string
- `master_key_id` : string


### `file_found`

- `action_id` : integer (optional)
- `file_id` : string
- `file_attrs` : object
- `file_url` : string
- `thumbnail_url` : string (optional)
- `url_expiry` : integer

The temporary `file_url` may be used to download the file.  `url_expiry`
specifies the time when `file_url` and `thumbnail_url` stop working.
`thumbnail_url` is specified if the file is of a common image type.


### `transcript_contents`

- `action_id` : integer
- `dialogue_members` : object (if applicable)
- `audience_metadata` : object (optional)
- `transcript_messages` : object array
- `message_id` : string (optional)

To identify the user who requested the audience, see which dialogue member has
the `queue_id` attribute.

`message_id` is set if `transcript_messages` doesn't contain everything.  It
may be used in a subsequent `get_transcript` call to get successive messages.

The `transcript_messages` array looks like this (the `message_user_id`,
`message_user_name` and `message_fold` properties are optional):

	"transcript_messages": [
		{
			"message_id":        "0fb74jl5",
			"message_time":      1320846070.265,
			"message_type":      "ninchat.com/text",
			"message_user_id":   "05kq2htc"
			"message_user_name": "Vance",
			"message_fold":      true,
			"payload": {
				"text": "Gold Five to Red Leader; lost Tiree, lost Dutch."
			}
		},
		...
	]

The messages are sorted from oldest to newest.


### `transcript_deleted`

- `action_id` : integer (optional)
- `dialogue_id` : string array (if applicable)


### `queue_transcripts_found`

- `action_id` : integer
- `queue_id` : string
- `queue_transcripts` : object array

The `queue_transcripts` array looks like this (the `rating` property is
optional):

	"queue_transcripts": [
		{
			"request_time":  1445592871.785086,
			"accept_time":   1445592877.183851,
			"finish_time":   1445592952.232474,
			"complete_time": 1445592955.341256,
			"dialogue_id":   ["05kq2htc", "38hj5ip5000eg"],
			"agent_id":      "05kq2htc",
			"rating":        -1
		},
		...
	]

The transcripts are sorted by `complete_time`; if the latest transcripts are
requested multiple times, new transcripts appear at the end.


### `queue_transcripts_deleted`

- `action_id` : integer
- `queue_id` : string
- `interval_begin` : float
- `interval_end` : float


### `tag_created`

- `action_id` : integer (optional)
- `realm_id` : string (if applicable)
- `tag_id` : string
- `tag_attrs` : object


### `tag_found`

- `action_id` : integer (optional)
- `realm_id` : string (if applicable)
- `tag_id` : string
- `tag_attrs` : object

`realm_id` is set if the tag belongs to a realm.  (Currently tags always belong
to a realm.)


### `tags_found`

- `action_id` : integer (optional)
- `realm_id` : string (if applicable)
- `tag_id` : string (if applicable)
- `tag_attrs` : object (if applicable)
- `tag_children` : object

`realm_id` is set if the tags belong to a realm (regardless of what was
specified in [`describe_tags`](#describe_tags)).

`tag_id` and `tag_attrs` are set if `tag_id` was specified in
[`describe_tags`](#describe_tags).

The `tag_children` object maps tag identifiers to objects containing tag
attributes and child tags (unless limited by the `tag_depth` specified in
[`describe_tags`](#describe_tags)):

	"tag_children": {
		"23456": {
			"tag_attrs": {
				"name": "My tag group"
			},
			"tag_children": {
				"34567": {
					"tag_attrs": {
						"name":      "My blue tag",
						"parent_id": "23456",
						"theme":     {"color": "#0000ff"}
					},
					"tag_children": {}
				},
				...
			}
		},
		...
	}


### `tag_updated`

- `action_id` : integer (optional)
- `realm_id` : string (if applicable)
- `tag_id` : string
- `tag_attrs` : object


### `tag_deleted`

- `action_id` : integer (optional)
- `realm_id` : string (if applicable)
- `tag_id` : string
- `tag_attrs` : object

`tag_attrs` contains the `parent_id` attribute, if the tag has one.


### `queue_stats_contents`

- `action_id` : integer
- `queue_stats` : object

Example queue stats:

	"queue_stats": {
		"2013091812": {
			"describe_count": 67,
			"request_count": 10,
			"audiences": [
				{
					"agent_id": "12345",
					"accept_count": 3,
					"finish_count": 2,
					"finish_duration_avg": 257.3,
					"ratings": {
						"-1": 1,
						"1": 1
					}
				},
				{
					"agent_id": "23456",
					"tag_ids": [
						"76543"
					],
					"vars": {
						"xyz": "100",
						"abcdef": "ghijkl"
					},
					"accept_count": 1,
					"finish_count": 2,
					"finish_duration_avg": 130.01,
					"ratings": {
						"0": 2
					}
				},
				...
			],
			"accept_delay_avg": 41.7,
			"drop_count": 6,
			"drop_delay_avg": 237.13
		},
		...
	}

The timestamp keys of the `queue_stats` object are composed of year, month, day
and hour (UTC).

The "audiences" array contains groups of statistics.  Each group is identified
by "agent_id", optional "tag_ids" and optional "vars".  See
[Audience metadata](#audience-metadata) for information about setting tag
identifiers and custom variables.


### `search_results`

- `action_id` : integer
- `users` : object (optional)
- `channels` : object (optional)

Following a `search` action, if neither of `users` and `channels` is defined,
this is the final response event.

The `users` and `channels` objects look like this:

	"users": {
		"12345": {
			"user_attrs": { "attr": "value", ... },
			"weight":     17.3
		},
		...
	}

	"channels": {
		"23456": {
			"channel_attrs": { "attr": "value", ... },
			"realm_id":      "34567",
			"weight":        0.1
		},
		...
	}


### `pong`

- `action_id` : integer (if specified in [`ping`](#ping))


### `ack`

- `action_id` : integer


Attributes
----------

Attributes are read-only unless stated otherwise.  Setting the value of an
attribute to `null` unsets the attribute.  The implicit value of an unset
boolean attribute is `false`.  Values with "time" type are represented as
non-negative integers, counting seconds since 1970-01-01 UTC.


### User

- `admin` : boolean

	The user is a site administrator.

- `connected` : boolean

	One or more devices are connected to the service.

- `deleted` : boolean

	User account has been deleted.

- `guest` : boolean (writable by self)

	Transient user account.  It will be deleted after the last session is
	closed (unless this attribute is unset before that).

- `iconurl` : string (unsettable by self)

	URL pointing to a small square profile picture.  This may be set indirectly
	by uploading icon image data; see the [`update_user`](#update_user) action
	for details.

- `idle` : time

	None of the connected devices are actively used.

- `info` : object (writable by self)

	Includes contact information:

		"info": {
			"company": "Oy Inichat Ab",
			"url":     "https://blog.example.org"
		}

- `name` : string (writable by self)

	Short nickname.

- `realname` : string (writable by self)

	Longer name.


### Identity

- `auth` : boolean

	A password is associated with the identity; it may be used for logging into
	the service.

- `blocked` : boolean

	Identity messaging opt-out.

- `pending` : boolean

	The identity has not been verified.

- `protected` : boolean

	The identity (e.g. email address) is visible to users who are members of
    the same realms as you are.

- `public` : boolean

	The identity (e.g. email address) is visible to other users.

- `rejected` : boolean

	It has been determined that the identity doesn't belong to the user.  (The
	identity may not be used for authentication.)


### Dialogue membership

- `audience_ended` : bool (writable by self)

	Indicates that the member has ended the dialogue which started via an
    audience queue.

- `queue_id` : string

	The dialogue was initiated by requesting an audience.

- `rating` : integer (writable by self)

	An optional rating given to your peer, in range [-1, 1].  (Set by
    audience-requesting users.)

- `writing` : bool (writable by self)

	May be used to indicate that the user has recently entered unsent text.
	(The API client is responsible for setting and clearing this indicator, if
	it chooses to implement it.)


### Channel

- `autohide` : boolean (writable by operators)

	Set the `autohide` channel member attribute for users who join the channel.

- `autosilence` : boolean (writable by operators)

	Set the `silenced` channel member attribute for users who join the channel.

- `blacklisted_message_types` : string array (writable by operators)

	Message types matching one of these patterns can't (currently) be sent to
	the channel.  This works in reverse compared to the `message_types`
	parameter of the [`create_session`](#create_session) action.  This also
	applies to the automatically generated `ninchat.com/info/*` messages.

- `closed` : boolean (writable by operators)

	Channel is in read-only state.

- `disclosed_since` : time (writable by operators)

	New members can see old messages since the specified time.  When set
	initially, the current time will be used.  After that, only a later time
	may be set, or the attribute may be unset.

- `followable` : boolean (writable by operators)

	The `follow_channel` action may be used.  The channel must also be
	disclosed, and must not be private.  Note: followable channels in realms
	are accessible by the public even when the `public` attribute is not set!


- `name` : string (writable by operators)

	Short subject name.

- `owner_id` : string

	User identifier.

- `private` : boolean (writable by operators)

	Invite only.

- `public` : boolean

	Channel is open for everyone despite being in a realm.

- `ratelimit` : string (writable by operators)

	"5/20" means 5 messages per 20 seconds.

- `suspended` : boolean (writable by owner)

	Similar to `closed`, but the channel doesn't count towards the owner's
	quota.

- `topic` : string (writable by operators)

	Longer subject description of the day.

- `upload` : string (writable by operators)

	Enables `send_file` action:

	- "member" enables it for all members.
	- "operator" enables it for members with the `operator` attribute.

- `verified_join` : boolean (writable by operators)

	The channel may not be joined without a verified identity.


### Channel membership

- `autohide` : boolean (writable by operators and moderators)

	Set the `message_hidden` parameter for messages sent to the channel.

- `moderator` : boolean (writable by operators)

	The user is a channel moderator.

- `operator` : boolean (writable by operators)

	The user is a channel operator.

- `silenced` : boolean (writable by operators and moderators)

	The user may not send messages to the channel.

- `since` : time

	Join time.

- `writing` : bool (writable by self)

	May be used to indicate that the user has recently entered unsent text.
	(The API client is responsible for setting and clearing this indicator, if
	it chooses to implement it.)


### Realm

- `name` : string

	Organization name.

- `owner_account` : object

	Visible only to realm operators.  Contains the "channels", "queues" and
	"queue_members" properties (see the `user_account` object of the
	[`session_created`](#session_created) event).

- `owner_id` : string

	User identifier.

- `suspended` : boolean

	Realm is in read-only state.

- `theme` : object (writable by operators)

	Customizes the color of the realm label:

		"theme": {
			"color": "#010b9b"
		}


### Realm membership

- `operator` : boolean

	The user is a realm operator.


### Queue

- `capacity` : integer (writable by queue members)

	Maximum number of allowed users in queue at a given time.

- `closed` : boolean (writable by queue members)

	New users may not join the queue at this time.

- `length` : integer

	Number of users currently in the queue.

- `name` : string (writable by realm operators)

	Queue name.

- `suspended` : boolean (writable by realm operators)

	The queue is in read-only state.  (This is similar to the `closed`
	attribute, but is not controlled by non-operator members.)

- `upload` : string (writable by realm operators)

	Enables `send_file` action in audience dialogues:

	- "member" enables it for both members.
	- "agent" enables it for the member who accepted the audience.
	- "customer" enables it for the member who requested the audience.


### File

- `name` : string (writable by owner)

	The filename.  Required.

- `type` : string

	Mime type of an image file.  Detected automatically.

- `size` : integer

	File size in bytes.  Calculated automatically.

- `thumbnail` : object

	Image file thumbnail dimensions in pixels
	(only exists if mime type is image file):

		"thumbnail": {
			"width": 128,
			"height": 96
		}


### Tag

- `name` : string (writable by realm operators)

	Tag name.

- `parent_id` : string (initializable by realm operators)

	Identifier of the parent tag, if this tag belongs to a tag group.

- `theme` : object (writable by realm operators)

	Customizes the color of the tag label:

		"theme": {
			"color": "#ff0000"
		}


### Puppet

- `name` : string (writable by master)

	User name.


User settings
-------------

- `highlight` : string array

	Highlight words to match against channel message text.  If a string ends
    with an asterisk (\*), the substring preceding the asterisk is used to
    match word prefixes instead of whole words.

- `highlight_name` : boolean

	Makes the current user name attribute a highlight word, regardless of the
	value of the `highlight` setting.

- `notifications` : object

	Enables desktop, audio, email and GCM/APNS notifications for channel,
	hightlight and/or private messages:

		"notifications": {
			"highlight":        false,
			"highlight_audio":  false,
			"highlight_email":  false,
			"highlight_mobile": false,
			"private":          false,
			"private_audio":    false,
			"private_email":    false,
			"private_mobile":   false,
			"channel":          false,
			"channel_audio":    false,
			"channel_mobile":   false
		}

- `proto` : boolean

	The user has received messages (via email), but has not activated the user
	account.


Error types
-----------

- `access_already_spent`
- `access_blocked`
- `access_denied`
- `access_expired`
- `action_not_supported`
- `audience_not_found`
- `channel_not_found`
- `channel_quota_exceeded`
- `connection_superseded`
- `deprecated`
- `file_not_found`
- `identity_already_exists`
- `identity_not_found`
- `internal`
- `message_dropped`
- `message_has_too_many_parts`
- `message_malformed`
- `message_not_supported`
- `message_part_too_long`
- `message_too_long`
- `message_type_too_long`
- `message_types_too_long`
- `permission_already_spent`
- `permission_denied`
- `permission_expired`
- `queue_is_closed`
- `queue_is_empty`
- `queue_is_full`
- `queue_is_suspended`
- `queue_member_quota_exceeded`
- `queue_not_found`
- `queue_quota_exceeded`
- `realm_already_exists`
- `realm_not_found`
- `realm_quota_exceeded`
- `request_malformed`
- `send_rate_limited`
- `session_buffer_overflow`
- `session_not_found`
- `tag_not_found`
- `upload_quota_exceeded`
- `user_not_found`


Message types
-------------

The server treats message types prefixed with "ninchat.com/" differently from
others: only the ones documented here are accepted by the server.  Messages
with other kind of message types are passed through without any additional
processing.


### `ninchat.com/file`

The payload consists of a single part with a JSON object containing the
following properties:

- `text` : string (optional)
- `files` : object list

The `files` list contains one or more objects with the following properties:

- `file_id` : string
- `file_attrs` : string


### `ninchat.com/info/*`

Info messages record relevant events in dialogue or channel history.  They are
generated by the server; ones sent by the client are rejected.  The payload
consists of a single part with a JSON object.  The object's properties depend
on the specific message type, as described below.

#### `ninchat.com/info/user`

- `user_id` : string
- `user_name` : string (optional)
- `user_name_old` : string (optional)
- `user_deleted` : boolean (optional)

A dialogue peer's or a channel member's `name` attribute changed, or a dialogue
peer was deleted.

#### `ninchat.com/info/channel`

- `channel_attrs_old` : object
- `channel_attrs_new` : object

Channel attributes changed.

#### `ninchat.com/info/join`

- `user_id` : string
- `user_name` : string (optional)
- `member_silenced` : boolean (optional)

A user joined the channel.

#### `ninchat.com/info/part`

- `user_id` : string
- `user_name` : string (optional)
- `cause` : string (optional)

A user left the channel.

The `cause` is "member_remove" if the message was caused by a `remove_member`
action.

#### `ninchat.com/info/member`

- `user_id` : string
- `user_name` : string (optional)
- `member_silenced` : boolean (optional)

A channel member's `silenced` attribute changed.

#### `ninchat.com/info/access`

- `user_id` : string
- `access_key` : string
- `channel_id` : string
- `channel_attrs` : object
- `realm_id` : string (optional)
- `realm_attrs` : object (optional)
- `realm_member` : boolean (optional)

You were invited to a channel and optionally to its realm.  `user_id` is the
invitor.


### `ninchat.com/link`

Link messages are used to send file share links.  The payload consists of a
single part with a JSON object containing properties described below.

- `name` : string
- `size` : integer
- `icon` : string
- `url` : string
- `thumbnail` : string (optional)


### `ninchat.com/metadata`

The payload consists of a single part with a JSON object containing the
following properties:

- `data` : object
- `time` : float (optional)

If `time` is specified, it overrides the `message_time` property of the
`message_received` event.  (It is used to indicate that the metadata change
happened some time before messaging was initiated.)


### `ninchat.com/notice`

Similar to `ninchat.com/text` (described below), but may only be sent to
channels, and only by channel operators.

	
### `ninchat.com/text`

Text messages are the basic message type, sent by clients.  The payload
consists of a single part with a JSON object containing a `text` property
(string):

	{"text":"This is the content of the message."}


Audience metadata
-----------------

Custom key-value pairs may be set via the `audience_metadata` action parameter,
or by sending a [`ninchat.com/metadata`](#ninchatcommetadata) message to a
audience dialogue.  Some metadata keys have predefined meanings, and are used
by Ninchat if set in a specific way:


### `secure`

See the [`request_audience`](#request_audience) action for details.


### `tag_ids`

String array containing tag identifiers.  Set by the acceptor of the audience
by sending a [`ninchat.com/metadata`](#ninchatcommetadata) message.  Used in
queue statistics.


### `vars`

Object containing key-value pairs (string values).  Set by the requester of the
audience via the [`request_audience`](#request_audience) action.  Used in queue
statistics.


Streaming Transports
====================

Both supported transport types support an initial service discovery step:

Before making a WebSocket connection or initiating HTTP long polling, the
client may discover a direct address by making a HTTP GET request to
`https://api.ninchat.com/v2/endpoint`.  The response contains a JSON object, or
a JavaScript statement (JSONP) if the `callback` query parameter is specified.
The object contains the `hosts` property (string array).  The client should try
the hosts in order until a transport connection succeeds.  The hosts array
shouldn't be used permanently; a fresh array must be requested when a new
session is to be created, or after looping through the array unsuccessfully for
a time.

A client implementation may choose to omit the service discovery step (e.g. for
simplicity) and use the `api.ninchat.com` hostname for transport connections.


WebSocket
---------

The URL format is `wss://HOST/v2/socket`, where `HOST` is an address aquired
during the service discovery step.  The WebSocket subprotocol is `ninchat.com`.

Actions and events consist of one or more frames.  The first one is a text
frame containing a JSON object with the `action` or `event` property (string),
the optional `frames` property (integer) and the parameter properties (see
Interface).  `resume_session` and `close_session`&mdash;when it is the initial
action&mdash;must contain the `session_id` property (string).  Any action may
also contain the latest received `event_id` (integer) to acknowledge events.

If `frames` is set and greater than 0, it specifies how many subsequent frames
form the payload.

The initial action on a connection must be `create_session`, `resume_session`,
`close_session` or one supporting sessionless operation.  A given connection
can't be used to open a new session after the `close_session` action and the
session can't be changed during a connection.

The client and the server may send empty (keep-alive) frames between
actions/events.  They should be ignored by the peer.

The frames may be text or binary.  Even if the client expects a frame
containing JSON or other text-based data, it must be able to handle binary
framing.


### Examples

Service discovery:

	GET /v2/endpoint HTTP/1.1
	Host: api.ninchat.com

	HTTP/1.1 200 OK
	Content-Type: application/json

	{
	  "hosts": ["192-0-43-10.ninchat.com", "192-0-43-11.ninchat.com"]
	}

...

Sent WebSocket frame:

	{
	  "action":       "send_message",
	  "action_id":    2,
	  "channel_id":   "04jqf8db",
	  "message_type": "ninchat.com/text",
	  "event_id":     6,
	  "frames":       1
	}

Sent WebSocket frame:

	{"text":"Gold Five to Red Leader; lost Tiree, lost Dutch."}

Received WebSocket frame:

	{
	  "event":             "message_received",
	  "action_id":         2,
	  "channel_id":        "04jqf8db",
	  "message_id":        "0fb74jl5",
	  "message_time":      1320846070,
	  "message_type":      "ninchat.com/text",
	  "message_user_id":   "05kq2htc",
	  "message_user_name": "Vance",
	  "event_id":          7,
	  "frames":            1
	}

Received WebSocket frame:

	{"text":"Gold Five to Red Leader; lost Tiree, lost Dutch."}


HTTP long polling
-----------------

The URL format is `https://HOST/v2/poll` (excluding query parameters), where
`HOST` is an address aquired during the service discovery step.

Actions and events consist of a single object containing an `action` or `event`
property (string), the optional `payload` property and the parameter properties
(see [Interface](#interface)).  Actions must also contain the `session_id`
property (string) when documentation doesn't state otherwise.  The
`resume_session` action should also contain the latest received `event_id`
(integer) to acknowledge events.

If `payload` is specified, its value represents a single-part payload.
Multi-part and JSON-incompatible payloads are not supported.  (Long poll
clients should accept only known JSON-based message types.)

The action object is provided in the `data` query parameter of a GET request
and the name of a JavaScript function is provided in the `callback` query
parameter.  The response body contains JavaScript code which invokes the
callback function with an array of event objects as a parameter.

`create_session` requests are responded to with an event specific to it
(providing the `session_id` needed for the other actions).  `resume_session`
requests block until there are asynchronous events to return or a timeout
occurs.  Other (well-formed) action requests get an empty response immediately;
any reply events are delivered by way of `resume_session`.


### Examples

Service discovery:

	GET /v2/endpoint?callback=connect HTTP/1.1
	Host: api.ninchat.com

	HTTP/1.1 200 OK
	Content-Type: application/javascript; charset=utf-8

	connect({
	  "hosts": ["192-0-43-10.ninchat.com", "192-0-43-11.ninchat.com"]
	});

Action:

	GET /v2/poll?data=%7B%22action%22%3A%22create_session%22%2C%22message_types%22%3A
	%5B%22ninchat.com%2Ftext%22%5D%7D&callback=func HTTP/1.1
	Host: 192-0-43-10.ninchat.com

	HTTP/1.1 200 OK
	Content-Type: application/javascript; charset=utf-8

	func([{
	  "event":           "session_created",
	  "session_id":      "4pfi0asg4pt56_0",
	  "user_id":         "0ebbjg1g",
	  "user_auth":       "2634d03q1tkt0",
	  "user_attrs":      { "name": "Elite" },
	  "user_settings":   {},
	  "user_identities": { "email": { "elite@example.com": { "pending": true } } },
	  "user_dialogues":  {},
	  "user_channels":   { "04jqf8db": { "channel_attrs": { "name": "Fibre" } } },
	  "user_realms":     {},
	  "event_id":        1
	}]);

Polling:

	GET /v2/poll?data=%7B%22action%22%3A%22resume_session%22%2C%22session_id%22%3A%22
	4pfi0asg4pt56_0%22%2C%22event_id%22%3A1%7D&callback=func HTTP/1.1
	Host: 192-0-43-10.ninchat.com

	HTTP/1.1 200 OK
	Content-Type: application/javascript; charset=utf-8

	func([{
	  "event":             "message_received",
	  "channel_id":        "04jqf8db",
	  "message_id":        "0fb74jl5",
	  "message_time":      1320846070,
	  "message_type":      "ninchat.com/text",
	  "message_user_id":   "05kq2htc",
	  "message_user_name": "Vance",
	  "event_id":          2,
	  "payload":           {"text":"Gold Five to Red Leader; lost Tiree, lost Dutch."}
	}]);


Sessionless HTTP Calling
========================

The call API supports a subset of the [Interface](#interface): the actions
which are practical without a connection-oriented transport may be invoked with
a HTTP request (without setting up long polling).  The
`https://api.ninchat.com/v2/call` URL may be accessed using GET and POST
methods, with `application/json`, `application/x-protobuf` and
`application/octet-stream` content types.

Actions and events use a JSON-encoded header (object) containing at least an
`action` or `event` property (string) and the parameter properties (see
[Interface](#interface)).  The `action_id` parameter may be omitted from
actions.  Events won't include the `event_id` parameter.


Requests
--------

Most actions require authentication (due to the lack of sessions):

1. The `caller_id` and `caller_auth` properties (strings) specify user agent
   login credentials.

2. The `caller_type`, `caller_name` and `caller_auth` properties (strings)
   specify identity credentials.  Currently only the "email" identity type is
   supported.

When the GET method or the POST method with `application/json` content type is
used, actions may also contain the `payload` property.  If specified, its value
represents a single-part payload.  Multi-part and JSON-incompatible payloads
are supported when using the POST method with `application/octet-stream`
content type.

POST content may be compressed with `deflate` (zlib) or `gzip` as the
`Content-Encoding`.


### GET

The `data` query parameter contains the action header with optional payload.

Example:

	GET /v2/call?data=%7B%22caller_id%22%3A%220ebbjg1g%22%2C%22caller_auth%
	22%3A%222634d03q1tkt0%22%2C%22action%22%3A%22join_channel%22%2C%22chann
	el_id%22%3A%2204jqf8db%22%7D HTTP/1.1
	Host: api.ninchat.com


### POST application/json

The request body contains the action header with optional payload.

Example:

	POST /v2/call HTTP/1.1
	Host: api.ninchat.com
	Content-Type: application/json

	{
	  "caller_id":   "0ebbjg1g",
	  "caller_auth": "2634d03q1tkt0",
	  "action":      "send_message",
	  "payload":     {"text":"hello world"},
	  ...
	}


### POST application/octet-stream

The request body contains the action header and payload parts using a binary
frame encoding similar to
[WebSocket](http://tools.ietf.org/html/rfc6455#section-5.2): each frame is
preceded by encoded frame size consisting of 1, 3 or 9 bytes:

- Sizes up to and including 125 are encoded as a single byte.

- Sizes 126-65535 are encoded as a byte with value 126, followed by two bytes
  with the size in network byte order (big endian).

- Sizes 65536 and up are encoded as a byte with value 127, followed by eight
  bytes with the size in network byte order (big endian).  The most significant
  bit of the eight-byte value must be zero; the (theoretical) maximum size can
  be represented by a signed 64-bit integer type.

Note that the most significant bit of the first byte must be zero.

Example:

	POST /v2/call HTTP/1.1
	Host: api.ninchat.com
	Content-Type: application/octet-stream

	\x52{"caller_id":"0ebbjg1g","caller_auth":"2634d03q1tkt0","action":"sen
	d_message",...}\x16{"text":"hello world"}


Responses
---------

The content type is chosen from the request's `Accept` header using the
following algorithm:

1. If there is only one event, it doesn't have a payload, and
   `application/json` is accepted, it is used.

2. If the event has a payload or there are multiple events, and
   `application/x-protobuf` is accepted, it is used.

3. If only one of `application/json`, `application/x-protobuf` and
   `application/octet-stream` is specified, it is used.  This may result in an
   incomplete response.

4. If no supported content types are accepted, the response will contain no
   data.

Support for additional content types may be added in the future, so using
wildcards in the `Accept` header (e.g. `*/*` or `application/*`) may suddenly
cause a response which the client can't handle.

Responses may contain one or more events, depending on the action.  In case of
an error, the "error" event is always the first one.


### application/json

The response body contains a list of event headers.  (Note that a payload is
not supported.)

Example:

	HTTP/1.1 200 OK
	Content-Type: application/json

	[{
	  "event":      "channel_joined",
	  "channel_id": "04jqf8db",
	  ...
	}]


### application/x-protobuf

The response body contains a serialized
[Protocol Buffers](https://developers.google.com/protocol-buffers/) message.
It is the `Response` message defined in [`call.proto`](call.proto); it supports
multiple events and payloads.

Example:

	HTTP/1.1 200 OK
	Content-Type: application/x-protobuf

	\x0a\x60\x0a\x5e{"channel_id":"103uok1j","message_id":"38f8589h","event
	":"history_results","history_length":1}\x0a\xcd\x01\x0a\xb7\x01{"histor
	y_length":0,"event":"message_received","channel_id":"103uok1j","message
	_user_id":"38f829b","message_time":1445514364,"message_type":"ninchat.c
	om/text","message_id":"38f8589h"}\x0a\x11{"text": "hello"}'


### application/octet-stream

The response body uses the same encoding as the corresponding request content
type, but currently only a single frame is supported.

