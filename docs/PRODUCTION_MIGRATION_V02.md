# Carolina EDGE Library API v0.2 Production Migration Candidate

Status: staging-qualified; production unchanged.

Validated staging commit: ac74e0b72ee294ef4c6ab942726efa75d4d400af

## Scope

This candidate adds publication/provenance controls to drills, seeds the 12 source-verified EDGE activities, isolates legacy/reference records from normal search, and expands retrieval across verified EDGE fields.

The production database currently contains 25 active drills on the legacy schema. The v0.2 migration is additive: no existing drill columns are removed.

## Required pre-deploy checks

1. Confirm production service remains on the current main branch and automatic deploy behavior is understood.
2. Confirm production Postgres is available.
3. Capture read-only baseline counts from the drills table.
4. Do not expose any drill unless both active=true and is_searchable=true.
5. Confirm the 12 seed IDs are unique and do not already exist.

## Deployment sequence

1. Merge this candidate to main only after explicit owner authorization.
2. Deploy one production instance against the existing production Postgres.
3. On startup, create any missing v0.2 drill columns with the additive migration.
4. Seed/update the 12 verified EDGE records by permanent EDGE ID.
5. Set legacy records to publication_status=LEGACY_HOLD, surface_policy=REFERENCE_ONLY, is_searchable=false.
6. Verify /health.
7. Verify /v1/drills returns exactly the approved searchable EDGE records expected for this seed release.
8. Verify direct GET of a legacy drill returns 404 from the public drill endpoint.
9. Verify source provenance fields on a known EDGE drill.
10. Run the Practice EDGE retrieval scenarios: angling, pressure, transition, 2v1, puck protection.
11. Verify no result lacks PUBLISH_NOW / READY FOR IMPORT.
12. Verify My Library/evaluation/contribution write paths remain healthy.

## Acceptance criteria

- API starts without migration errors.
- Existing 25 production drill records remain present after migration.
- No legacy/reference drill becomes publicly searchable.
- Exactly the approved seed records are newly searchable.
- Practice EDGE retrieval scenarios return at least one relevant approved record.
- No unapproved publication state leaks through search.
- Existing write workflows continue to function.
- No source text is overwritten by adaptation text.

## Rollback

If any acceptance criterion fails:

1. Stop further promotion immediately.
2. Roll the service back to the previous production deploy/commit.
3. Leave additive database columns in place; they are backward-compatible with the prior application version.
4. Do not delete existing legacy records.
5. If seed records were inserted, set their active=false and is_searchable=false before retrying a future migration.
6. Confirm the prior production endpoints and write workflows are healthy.
7. Record the failed criterion and fix only in staging before another production attempt.

## Staging evidence

- v0.2 base acceptance suite: 6 passed.
- Expanded Practice EDGE retrieval/isolation suite: 8 passed.
- Staging API service starts successfully.
- Legacy/reference leakage checks passed.
- Staging search expanded to title, game problem, target behaviors, search tags, representative information, player decisions, source text, and coach notes.

## Known non-blocking warnings

- FastAPI/Starlette test-client deprecation warning regarding httpx.
- SQLAlchemy warning for datetime.utcnow().
These did not cause test failures and are not part of this release scope.

## Explicit non-actions

- Do not publish the 18 EDGE Adapt records in this release.
- Do not surface C/reference or archived records.
- Do not delete legacy drills.
- Do not change production until owner authorization.
