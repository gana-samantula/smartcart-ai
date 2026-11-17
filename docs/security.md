# SmartCart AI — Security: Authentication Design

Status: implemented for the backend in Phase 2. Not yet reviewed by a security team, and not yet
covered by the mobile client. Limits are listed at the end.

## Token model (ADR-014)

- Access and refresh tokens are 256-bit random strings (`secrets.token_urlsafe(32)`). They are
  opaque, so no JWT library is used.
- Only SHA-256 digests are stored, in `auth_sessions`. A database leak does not reveal usable
  tokens.
- Access tokens last 15 minutes. Refresh tokens last 30 days. Both settings are configurable.
- `POST /auth/refresh` rotates both tokens in place. The old access token stops working at once.
- Replay detection: each session keeps the previous refresh digest. Presenting a rotated-out
  refresh token revokes the whole session and writes `auth.refresh_replay_detected`.
- Trade-off: each authenticated request costs one indexed lookup. This is acceptable at the
  current scale. Revisit if authentication becomes a bottleneck.

## Passwords

- Hashed with scrypt (N=2^15, r=8, p=1, 64 MiB memory limit) from the standard library. Each hash
  stores its own parameters and salt, so the work factor can be raised later.
- Length 12 to 128 characters. The upper bound keeps hashing cost bounded.
- Comparisons use `hmac.compare_digest`. Malformed hashes never match.
- Unknown emails still run a full hash check against a dummy hash, so response timing does not
  reveal which accounts exist.

## Account enumeration

- Login failures return the same code and message for a wrong password and an unknown email.
- Password-reset requests return 202 whether or not the account exists.
- **Accepted trade-off:** registration returns 409 `email_already_registered`, which reveals that
  an account exists. Clients need that to show a useful message. Revisit if this becomes a
  requirement.

## Password recovery

- Reset tokens expire after 30 minutes by default and are single-use.
- Requesting a new reset invalidates earlier unused tokens for that account.
- Confirming a reset ends all sessions for the account.
- Reset tokens are sent through the email interface only. They are never written to logs.
- **No production email provider exists yet.** Staging and production refuse to start with the
  current settings. Development uses `console`, which prints the token to stdout, and tests use
  `memory`.

## Sessions and changes

- Changing a password ends every other session. The current session stays signed in.
- Account deletion removes the user, sessions and reset tokens through database cascades.
- `audit_logs` keeps the event name and user ID after deletion, so the audit trail survives. The
  user ID is still personal data, so retention of that table needs a policy (see
  `docs/privacy.md`, not yet written).

## Rate limiting

- Login, registration and reset requests are limited per client address, per minute
  (default 10).
- The limiter is in-process. With several workers or replicas, the effective limit multiplies.
  A Redis-backed limiter is required before running more than one replica.
- The limit is keyed on the client address only. Per-account limits are not implemented.

## Audit events

`auth.registered`, `auth.login`, `auth.login_failed`, `auth.logout`,
`auth.refresh_replay_detected`, `auth.password_reset_requested`,
`auth.password_reset_completed`, `auth.password_changed`, `auth.account_deleted`.

Events record the name, the user ID when known, and the time. They never record emails, passwords
or tokens.

## Known limits

- No multi-factor authentication.
- No account lockout beyond rate limiting.
- No device or IP tracking on sessions.
- No email verification at registration.
- Rate limiting is per process, as described above.
- Google and Apple sign-in are not implemented.
- The refresh-replay check revokes the session even if a legitimate client retried after losing a
  response. That is a deliberate safety trade-off.
