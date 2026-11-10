# maps-leads

Builds an owned B2B lead list from Google Maps: scrape a whole market area by
area, dedupe and qualify it, pull owner-inbox emails from each business's own
website, score every account, and export sending-ready CSVs.

Python 3.11+, standard library only. Nothing to install.

## Pipeline

| Stage | Command | What it does |
|---|---|---|
| 1. Market | `plan` | Builds every category x area search and prints the query count and cost before anything is spent |
| 2. Scrape | `scrape` | Runs the searches through Serper's Maps API. Resumable; failed queries retry on the next run |
| 3. Clean | `clean` | Dedupes by Google listing, phone and website domain; cleans names; cuts chains; applies your ICP filters |
| 4. Contacts | `enrich` | Reads each qualified website for `info@`/`office@`/owner emails, verifies them, dedupes by email |
| 5. Score | `score` | Fit score + intent score from verifiable signals, then tier A/B/C |
| Export | `export` | `emails_business.csv`, `emails_personal.csv`, `call_list.csv`, `all_leads.csv` |

`run` does stages 2 to 5 plus the export. `stats` prints the funnel.

## Setup

```bash
cd maps-leads
cp .env.example .env                  # add SERPER_API_KEY (serper.dev)
cp config.example.toml config.toml    # describe your market
```

**Storage.** With `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env` the list
lives in Supabase: run `supabase/migrations/0001_maps_leads.sql` in the SQL
editor once to create the three tables. Use the service-role key; the tables
have row level security on with no policies, so the anon key cannot read them.
With both left blank, everything goes to a local `maps_leads.db` SQLite file,
which is handy for a first test.

## Run it

```bash
python -m maps_leads zips US        # postal mode only: free postal-code list from GeoNames
python -m maps_leads plan --dry-run # size and cost, queues nothing
python -m maps_leads plan           # queue the searches
python -m maps_leads scrape --limit 20   # cheap trial on 20 searches
python -m maps_leads run            # everything
python -m maps_leads stats
```

## Covering any country

Every Maps search caps its results, so the system searches many small areas.
Pick the mode in `[areas]`:

- **`postal`**: one search per postal code (`"roofer 75201"`). `zips <country>`
  downloads the list for about 100 countries; any CSV with a
  `zip`/`code`/`postcode` column also works. `regions` filters by state.
- **`grid`**: one search per cell of a lat/lng grid over a bounding box. Use
  this where postal codes do not work on Maps (Nigeria, UAE, much of Africa and
  the Middle East). Start with `cell_km = 3` and go smaller in dense cities:
  if `stats` shows many queries returning the full 60 results, cells are too big.

## Where each rule lives

- **Dedupe, pass 1 (business):** overlapping areas return the same listing many
  times; it is stored once by Google id. Listings sharing a phone or a website
  domain are grouped, the one with the most reviews is kept, and the group size
  becomes `location_count`. Shared hosts (Facebook, Linktree, Wix...) are never
  used as a dedupe key.
- **Chains:** `max_locations` cuts groups above that size; `min_locations`
  targets them instead.
- **Qualify before enriching:** website, minimum reviews, rating range,
  category keywords, excluded names. Rejected rows keep a `reject_reason`.
- **Emails:** only addresses on the business's own domain or a freemail box are
  kept, so a web agency's address in the footer is never collected.
- **Dedupe, pass 2 (email):** `maps_contacts` is keyed by email. An address
  published on several listings belongs to the largest one; the others are
  recorded in `also_on` and left out of every export.
- **Verification:** with `MILLIONVERIFIER_API_KEY` set, each mailbox is checked
  (`ok`, `catch_all`, `invalid`). Without it only a free MX lookup runs
  (`mx_ok`), which proves the domain takes mail, not that the mailbox exists.
  Verify properly before sending at volume.
- **Scoring:** fit (0 to 50) covers live site, usable email, phone, review
  count, rating. Intent adds your points for `hiring`, `runs_ads`,
  `review_growth`, plus any `[[score.keyword_signals]]` you define (one
  question each, matched against website text).
- **Sending split:** freemail addresses export to their own file so they can go
  through a separate sending account. `first_name` is left blank on purpose.

## Keeping the list

Every 30 to 60 days:

```bash
python -m maps_leads plan --refresh   # re-queue every search
python -m maps_leads run
python -m maps_leads export --since 2026-12-01   # only businesses first seen since then
```

Existing rows are updated in place, new businesses are added, enrichment is
kept, and a jump in review count since the last scrape becomes the
`review_growth` intent signal. `enrich --force` re-reads every website.

## Limits

- Serper's Maps results carry no review text or review dates, so
  "reviews mention slow quotes" style signals are not available; review growth
  between scrapes stands in for a recent-review spike.
- No owner-name lookup, paid email waterfall, AI qualification or sending.
  The exports are the hand-off point to those tools.
- Name cleaning is rule-based. It cannot tell an all-caps word from an
  acronym ("ABC ROOFING" becomes "Abc Roofing"); skim Tier A names before sending.
- A site that fails to load is marked `dead`. If your connection dropped
  mid-run, use `enrich --force`.
- Cold email is regulated (CAN-SPAM, GDPR/PECR, NDPR and others). Include an
  opt-out and a physical address, and check the rules for the country you send to.

## Verification

`python -m unittest discover -s tests` runs unit tests plus a full pipeline run
against a fake Serper API and fake websites, covering pagination, overlap
merging, both dedupe passes, the chain filter, email extraction, scoring,
exports and a re-scrape. The Supabase client is tested at the request level
only, and no live Serper call has been made from this repo yet.
