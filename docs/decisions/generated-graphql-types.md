# ADR: Generated GraphQL types are build artifacts

- Status: Accepted
- Date: 2026-11-25

## Context

The frontend had a hand-authored `src/types/graphql.ts` plus a generated
`src/graphql/generated/` directory. Codegen was not re-run after schema changes,
so the generated files were stale and produced TypeScript errors.

## Decision

There is one type source at a time. The hand-authored
`src/types/graphql.ts` is canonical until codegen is re-run against the fixed
backend. `codegen.ts` outputs a single ignored file,
`src/graphql/generated.ts`, which is not committed.

## Consequences

- No stale generated directory is imported.
- `npm run graphql:generate` regenerates types when needed.
- `frontend/src/graphql/generated.ts` is in `.gitignore`.
