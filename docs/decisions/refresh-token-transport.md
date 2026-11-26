# ADR: Refresh token transport uses `X-Refresh-Token`

- Status: Accepted
- Date: 2026-11-25

## Context

The backend issues access and refresh tokens, but the refresh mutation needs a
way to receive the refresh token. The frontend previously dropped the refresh
token from the login/register payload.

## Decision

The client sends the refresh token in the `X-Refresh-Token` HTTP header. The
`AuthPayload` type includes `refreshToken`, and login/register responses return
both tokens. The `refreshToken` mutation returns a new access token.

## Consequences

- `graphqlClient` supports `{ accessToken, refreshToken }` and sets both headers.
- `authStore` persists both tokens.
- Login and register UI select `refreshToken` from `AuthPayload`.
- The header is documented in `docs/api/graphql-schema.md`.
