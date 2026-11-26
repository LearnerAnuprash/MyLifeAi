# ADR: `recurrence_exceptions` stores occurrence timestamps

- Status: Accepted
- Date: 2026-11-25

## Context

The schema originally described `events.recurrence_exceptions` as an array of
event IDs. Recurring exceptions are identified by the occurrence they replace,
not by the ID of the replacement event, and expansion needs to compare start
times.

## Decision

`recurrence_exceptions` is `TIMESTAMPTZ[]` in PostgreSQL, `List[DateTime]` in
the GraphQL type, and a list of timezone-aware datetimes in services. Expansion
normalizes values to UTC before comparing them with generated occurrences.

## Consequences

- Migration `001_initial_schema.py` uses `ARRAY(DateTime(timezone=True))`.
- Adding an exception appends the skipped occurrence timestamp.
- Expansion skips matching occurrences regardless of the replacement event ID.
- Clients receive `recurrenceExceptions: [DateTime!]!`.
