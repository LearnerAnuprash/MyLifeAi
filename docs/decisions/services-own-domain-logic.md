# ADR: Services own domain logic; models are persistence-only

- Status: Accepted
- Date: 2026-11-25

## Context

`User` and other SQLAlchemy models had accumulated business methods, GraphQL
conversion helpers, and service calls. This duplicated logic across services and
made models depend on GraphQL types.

## Decision

SQLAlchemy models contain only columns, relationships, and persistence-level
helpers. Domain logic lives in `app/services/*`. Model-to-GraphQL conversion
lives in `app/graphql/serializers.py`.

## Consequences

- Services are the single entry point for domain operations.
- GraphQL resolvers stay thin and delegate to services.
- Models can be used in workers and tests without GraphQL imports.
