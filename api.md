This document describes version 1 of the open [Ninchat](https://ninchat.com)
API.  It will be extended over time, without causing regressions to conforming
client applications.  (If a new, backward-incompatible API version is released,
it will be accessible using a new endpoint address or protocol identifier.)

Copyright &copy; 2012-2013 Somia Reality Oy.  All rights reserved.


Interface
=========

Clients send actions to the server, which sends events to clients.  Action and
event parameter values are represented as JSON types.

Most actions support or require the `action_id` parameter, which may be used to
detect success or failure of the action.  When the client receives (at least)
one event with the corresponding `action_id`, the action has succeeded, unless
the event was `error`.  The values should be ascending integers, starting at 1,
over the lifetime of the client instance's state (even across sessions).  If no
response event is received, the client may retry the action (e.g. after
reconnecting) with the same `action_id` value.

In addition to the parameters listed below, most events contain the
monotonically ascending `event_id` integer parameter (starting at 1).  Such
events are buffered by the server until they are acknowledged by the client, so
that they can be retransmitted if the network connection is lost during a
session.  (Events without an `event_id` are connection-specific.)  The
acknowledgement procedure is transport-specific (see
[Transports](#transports)).  Failure to acknowledge events results in session
buffer overflow.

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

_`session_id` must not be specified_ (see [Transports](#transports))

- `user_id` : string (optional)
- `user_auth` : string (optional)
- `user_attrs` : object (optional)
- `user_settings` : object (optional)
- `identity_type` : string (optional)
- `identity_name` : string (optional)
- `identity_auth` : string (optional)
- `access_key` : string (optional)
- `message_types` : string array

Reply event: [`session_created`](#session_created)

There are four modes of operation:

1. If `user_id` and `user_auth` are specified, a new session for an existing
   user is created.
2. If `identity_type`, `identity_name` and `identity_auth` are specified, a new
   session for an existing user is created.  The identity type and name must be
   verified for a user.
3. If `access_key` is specified, a new session for an existing user is created.
   The access key configuration determines the user.
4. Otherwise a new user is created.

Accepted message types are specified as a list of strings to compare against
incoming message types.  If a string ends with an asterisk (\*), the substring
preceding the asterisk is used to match prefixes instead of whole strings.  The
"*" string accepts all messages.  An empty array rejects all messages.

If the authentication token or access key is invalid or has been revoked, the
error type will be `access_denied`.  This condition is permanent:
`create_session` won't succeed later with the same parameters.


### `resume_session`

Receive or acknowledge events of an existing session.  See
[Transports](#transports) for details.


### `update_session`

- `session_idle` : boolean (optional)
- `channel_id` : string (optional)
- `user_id` : string (optional)
- `message_id` : string (optional)

Client-assisted idle user and unread message tracking.


### `close_session`

See [Transports](#transports) for details.


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
- `user_auth` : string

Reply event: [`user_deleted`](#user_deleted)

You must repeat `user_auth` here to avoid accidents and mischief.


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

A secret authentication token (password) is associated with the identity if
`identity_auth_new` is specified.


### `request_identity_verify_access`

_`session_id` not required_

- `action_id` : integer (optional)
- `identity_type` : string
- `identity_name` : string

Reply event: `access_created` (without `access_key`)

Resend an email identity verification link if the identity is still pending
verification.  (In other words, `identity_type` must be "email" for now.)


### `verify_identity`

_`session_id` not required_

- `action_id` : integer (optional)
- `access_key` : string
- `identity_accept` : boolean

Reply event: [`identity_updated`](#identity_updated)

Accepts or rejects a pending user identity.


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

_`session_id` not required_

- `action_id` : integer (optional)
- `identity_type` : string
- `identity_name` : string

Reply event: [`access_created`](#access_created) (without `access_key`)

Create and send an access key to the specified email address if it's a verified
email identity.  (In other words, `identity_type` must be "email" for now.)
The access key may be used to reset the password associated with the identity.


### `reset_identity_auth`

_`session_id` not required_

- `access_key` : string
- `identity_auth_new` : string

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


### `create_channel`

- `action_id` : integer
- `channel_attrs` : object (optional)
- `realm_id` : string (optional)

Reply event: [`channel_created`](#channel_created)

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


### `join_channel`

- `action_id` : integer
- `channel_id` : string (optional)
- `access_key` : string (optional)

Reply events: [`channel_joined`](#channel_joined) and
              [`realm_joined`](#realm_joined) (if applicable)

There are two modes of operation:

1. `channel_id` specifies the channel to be joined.  It must not be in a realm
   or it must be in one of the user's realms.
2. `access_key` grants permission to join a channel in a realm.  The access key
   configuration determines the channel to be joined.  The
   [`realm_joined`](#realm_joined) event indicates that the user was granted
   access to the channel's realm in addition to the channel (depending on the
   access key configuration).


### `part_channel`

- `action_id` : integer
- `channel_id` : string

Reply event: [`channel_parted`](#channel_parted)


### `create_realm`

- `action_id` : integer
- `realm_attrs` : object (optional)
- `channel_attrs` : object (optional)

Reply events: [`realm_joined`](#realm_joined) and
              [`channel_joined`](#channel_joined) (if applicable)

Creates a realm, and an optional initial channel if `channel_attrs` is defined.
The session user will become the owner of both.


### `describe_realm`

- `action_id` : integer
- `realm_id` : string

Reply event: [`realm_found`](#realm_found)


### `update_realm`

- `action_id` : integer
- `realm_id` : string
- `realm_attrs` : object

Reply event: [`realm_updated`](#realm_updated)


### `delete_realm`

- `action_id` : integer
- `realm_id` : string

Reply event: [`realm_deleted`](#realm_deleted)


### `update_member`

- `action_id` : integer
- `channel_id` : string (optional)
- `realm_id` : string (optional)
- `user_id` : string
- `member_attrs` : object

Reply event: [`channel_member_updated`](#channel_member_updated) or
             [`realm_member_updated`](#realm_member_updated)

Sets or clears a channel or realm membership attributes for a user.


### `remove_member`

- `action_id` : integer
- `channel_id` : string (optional)
- `realm_id` : string (optional)
- `user_id` : string

Reply event: [`channel_member_parted`](#channel_member_parted) or
             [`realm_member_parted`](#realm_member_parted)

Kicks a user out of a channel or a realm.


### `send_message`

- `action_id` : integer (optional)
- `channel_id` : string (optional)
- `user_id` : string (optional)
- `identity_type` : string (optional)
- `identity_name` : string (optional)
- `message_type` : string
- `message_ttl` : float (optional)

Reply event: [`message_received`](#message_received) or none (if `action_id` is
             not specified)

Message content is provided in the payload (see [Transports](#transports)).
The content may not be empty: it must contain one or more parts (but the
individual parts may be zero-length).

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


### `load_history`

- `action_id` : integer
- `channel_id` : string (optional)
- `user_id` : string (optional)
- `message_types` : string array (optional)
- `message_id` : string (optional)
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
- `realm_member` : boolean (optional)
- `user_id` : string (optional)

Reply event: [`access_created`](#access_created)

Creates an access key for use with [`create_session`](#create_session) or
[`join_channel`](#join_channel).

Access types:

- "session" keys may be used in `create_session` actions.
- "channel" keys may be used in a single `join_channel` action.  If
  `realm_member` is true, the invited user will also join the realm of the
  channel (if any).  If `user_id` is specified, the invite can only be used by
  that user, and an info message is sent to that user (see
  [Message types](#message-types)).


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

_`session_id` not required_

- `action_id` : integer (optional)
- `access_key` : string

Reply event: [`access_found`](#access_found)


### `search`

- `action_id` : integer
- `search_term` : string

Reply events: [`search_results`](#search_results) multiple times

Searches users and channels by name or realname prefixes.


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

If specified, `session_host` contains a hostname which should be used in
subsequent connections for this session.

If a new user was created, then `user_auth` contains a generated password which
may be used in future [`create_session`](#create_session) actions by the
client.

The `user_account` object contains information about channel and realm quota
and service subscription (optional):

	"user_account": {
		"channels": {
			"quota":             10,
			"available":         3
		},
		"realms": {
			"quota":             3,
			"available":         2
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
optional `dialogue_members` object and the optional `dialogue_status` string:

	"user_dialogues": {
		"12345": {
			"dialogue_members": {
				"23456": { "attr": "value", ... },
				"65432": { "attr": "value", ... }
			},
			"dialogue_status": "highlight"
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
- `dialogue_members` : object (if the session user has a dialogue with the user)
- `dialogue_status` : string (if the session user has a dialogue with the user
                              and there are unread messages)

The `dialogue_members` object consists of two user identifiers mapped to
dialogue membership attributes:

	"dialogue_members": {
		"12345": { "attr": "value", ... },
		"54321": { "attr": "value", ... }
	}

The dialogue membership attributes objects will be empty unless the user is the
session user.

If set, the value of `dialogue_status` will be "highlight".


### `user_updated`

- `action_id` : integer (if applicable)
- `user_id` : string
- `user_attrs` : object
- `user_settings` : object (if the user is the session user)
- `user_account` : object (if the user is the session user)


### `user_deleted`

- `action_id` : integer (if applicable)
- `user_id` : string


### `identity_found`

- `action_id` : integer (if applicable)
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object (if belonging to the session user)


### `identity_created`

- `action_id` : integer (if applicable)
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object


### `identity_updated`

- `action_id` : integer (if applicable)
- `identity_type` : string
- `identity_name` : string
- `identity_attrs` : object


### `identity_deleted`

- `action_id` : integer (if applicable)
- `identity_type` : string
- `identity_name` : string


### `dialogue_updated`

- `action_id` : integer (if applicable)
- `user_id` : string
- `dialogue_members` : object


### `channel_found`

- `action_id` : integer (if applicable)
- `channel_id` : string
- `channel_attrs` : object
- `channel_members` : object (if the session user is a member)
- `channel_status` : string (if the session user is a member and there are
                             unread messages)
- `realm_id` : string (if applicable)

The `channel_members` object consists of user identifiers mapped to objects
containing the `user_attrs` object and the `member_attrs` object (the
channel-specific attributes of the user):

	"channel_members": {
		"12345": {
			"user_attrs": { "attrs": "value", ... },
			"member_attrs": { "attrs": "value", ... }
		},
		...
	}

If set, the value of `channel_status` will be "unread" or "highlight".


### `channel_joined`

- `action_id` : integer (if applicable)
- `channel_id` : string
- `channel_attrs` : object
- `channel_members` : object
- `realm_id` : string (if applicable)

The session user created a new or joined an existing channel.


### `channel_parted`

- `action_id` : integer (if applicable)
- `channel_id` : string

The session user left or was removed from a channel.


### `channel_updated`

- `action_id` : integer (if applicable)
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

Someone else joined a channel.


### `channel_member_parted`

- `action_id` : integer (if applicable)
- `channel_id` : string
- `user_id` : string

Someone else left or was removed from a channel.


### `channel_member_updated`

- `action_id` : integer (if applicable)
- `channel_id` : string
- `user_id` : string
- `member_attrs` : object


### `realm_found`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `realm_attrs` : object
- `realm_members` : object (if the session user is a member)

`realm_members` is analogous to [`channel_members`](#channel_found) described
above.


### `realm_joined`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `realm_attrs` : object
- `realm_members` : object

The session user created a new or joined an existing realm.


### `realm_parted`

- `action_id` : integer (if applicable)
- `realm_id` : string

The session user left or was removed from a realm.


### `realm_updated`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `realm_attrs` : object


### `realm_deleted`

- `action_id` : integer (if applicable)
- `realm_id` : string


### `realm_member_joined`

- `realm_id` : string
- `user_id` : string
- `user_attrs` : object
- `member_attrs` : object

Someone else joined a realm.


### `realm_member_parted`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `user_id` : string

Someone else left or was removed from a realm.


### `realm_member_updated`

- `action_id` : integer (if applicable)
- `realm_id` : string
- `user_id` : string
- `member_attrs` : object


### `message_received`

- `action_id` : integer (if applicable)
- `channel_id` : string (if applicable)
- `user_id` : string (if applicable)
- `message_id` : string
- `message_time` : float
- `message_type` : string
- `message_user_id` : string (if applicable)
- `message_user_name` : string (if applicable)
- `message_ttl` : float (if applicable)
- `history_length` : integer (if succeeding a `history_results` event)

Message content is optionally provided in the payload (see
[Transports](#transports)).  The content may be omitted in some cases,
including but not limited to the situation when the sender session hasn't
subscribed to the sent message type, but expects a reply event.

`message_user_id` and `message_user_name` are not set for system messages (see
[Message types](#message-types)).


### `history_results`

- `action_id` : integer
- `channel_id` : string (if applicable)
- `user_id` : string (if applicable)
- `history_length` : integer (if applicable)


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


Attributes
----------

Attributes are read-only unless stated otherwise.  Setting the value of an
attribute to `null` unsets the attribute.  The implicit value of an unset
boolean attribute is `false`.  Time values are represented as non-negative
integers, counting seconds since 1970-01-01 UTC.


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

- `public` : boolean

	The identity (e.g. email address) is visible to other users.

- `rejected` : boolean

	It has been determined that the identity doesn't belong to the user.  (The
	identity may not be used for authentication.)


### Dialogue membership


### Channel

- `autosilence` : boolean (writable by operators)

	Set the `silenced` channel member attribute for users who join the channel.

- `blacklisted_message_types` : string array (writable by operators)

	Message types matching one of these patterns can't (currently) be sent to
	the channel.  This works in reverse compared to the `message_types`
	parameter of the [`create_session`](#create_session) action.  This also
	applies to the automatically generated `ninchat.com/info/*` messages.

- `name` : string (writable by operators)

	Short subject name.

- `owner_id` : string

	User identifier.

- `private` : boolean (writable by operators)

	Invite only.

- `public` : boolean

	Channel is open for everyone despite being in a realm.

- `suspended` : boolean

	Channel is in read-only state.

- `topic` : string (writable by operators)

	Longer subject description of the day.


### Channel membership

- `operator` : boolean (writable by operators)

	The user is a channel operator.

- `silenced` : boolean (writable by operators)

	The user may not send messages to the channel.

- `since` : time

	Join time.


### Realm

- `name` : string

	Organization name.

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


Settings
--------

- `notifications` : object

	Enables audio, email and desktop notifications for channel, hightlight
	and/or private messages:

		"notifications": {
			"channel_audio":   false,
			"highlight_audio": false,
			"private_audio":   false,
			"highlight_email": false,
			"private_email":   false,
			"channel":         false,
			"highlight":       false,
			"private":         false
		}

- `proto` : boolean

	The user has received messages (via email), but has not activated the user
	account.


Error types
-----------

- `access_denied`
- `access_expired`
- `action_not_supported`
- `channel_not_found`
- `channel_quota_exceeded`
- `connection_superseded`
- `deprecated`
- `identity_already_exists`
- `identity_not_found`
- `internal`
- `message_has_too_many_parts`
- `message_malformed`
- `message_not_supported`
- `message_part_too_long`
- `message_too_long`
- `message_type_too_long`
- `message_types_too_long`
- `permission_denied`
- `realm_already_exists`
- `realm_not_found`
- `realm_quota_exceeded`
- `request_malformed`
- `session_buffer_overflow`
- `session_not_found`
- `user_not_found`


Message types
-------------

The server treats message types prefixed with "ninchat.com/" differently from
others: only the ones documented here are accepted by the server.  Messages
with other kind of message types are passed through without any additional
processing.


### `ninchat.com/info/*`

Info messages record relevant events in dialogue or channel history.  They are
generated by the server; ones sent by the client are rejected.  The payload
consists of a single part with a JSON object.  The contents depend on the
specific message type.

#### `ninchat.com/info/user`

	- `user_id` : string
	- `user_name` : string (optional)
	- `user_name_old` : string (optional)
	- `user_deleted` : boolean (optional)

	A dialogue peer's or a channel member's `name` attribute changed, or a
	dialogue peer was deleted.

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

	A user left the channel.

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

	You were invited to a channel and optionally to its realm.  `user_id` is
	the invitor.


### `ninchat.com/link`

Link messages are used to send file share links.  The payload consists of a
single part with a JSON object containing properties described below.

- `name` : string
- `size` : integer
- `icon` : string
- `url` : string
- `thumbnail` : string (optional)


### `ninchat.com/notice`

Similar to `ninchat.com/text` (described below), but may only be sent to
channels, and only by channel operators.

	
### `ninchat.com/text`

Text messages are the basic message type, sent by clients.  The payload
consists of a single part with a JSON object containing a `text` property
(string):

	{"text":"This is the content of the message."}


Transports
==========

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


HTTP Long Poll
--------------

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

