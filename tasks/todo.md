# Maps lead prospecting system: plan

Decisions (from the user): any country (postal-code + lat/lng grid modes), Serper.dev,
Supabase storage, stages 1-5 + export (no sending, no AI agents in this build).

- [x] Stage 1: config + query builder (category x area), size/cost check before spending
- [x] Stage 2: resumable Serper Maps scraper, postal-code and grid modes
- [x] Stage 3: business-level dedupe (place id, phone, domain), name cleaning, chain filter, qualification
- [x] Stage 4: website email scrape (info@/office@...), verification, email-level dedupe
- [x] Stage 5: fit + intent scoring on verifiable signals, A/B/C tiers
- [x] Export: per-stream CSVs (business emails, personal emails, call list)
- [x] Storage: Supabase (PostgREST) with a local SQLite fallback for dev/tests
- [x] Re-scrape support: first_seen/last_seen, review growth as an intent signal
- [x] Tests: unit + end-to-end against a fake Serper API and fake websites
- [ ] Apply the migration to a Supabase project (needs the user to pick the project)
- [ ] Live run with a real Serper key (no key and no outbound network in the build sandbox)

## Review
- 7 tests pass (`python -m unittest discover -s tests` in `maps-leads/`), including an
  end-to-end run against a fake Serper API and fake websites.
- CLI run (`plan`, `run`, `stats`) checked against the same fake API with SQLite storage.
- Not yet exercised: a live Serper call, and live reads/writes against Supabase
  (request shapes are unit-tested; the migration has not been applied to any project).
