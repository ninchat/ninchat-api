Ninchat WebRTC ports
--------------------

| Protocol | Transport | Port |
| -------- | --------- | ---- |
| STUN     | UDP       | 3478 |
| STUN     | TCP       | 3478 |
| STUN     | TCP       |  443 |
| TURN     | UDP       | 3478 |
| TURN     | TCP       | 3478 |
| TURN     | TCP       |  443 |
| TURNS    | UDP + TLS | 5349 |
| TURNS    | TCP + TLS | 5349 |
| TURNS    | TCP + TLS |  443 |

- UDP transport offers best performance.
- HTTPS port 443 is used as a fallback (TCP only).
- Communication is end-to-end encrypted regardless of TLS support.

