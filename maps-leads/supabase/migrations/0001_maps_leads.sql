-- Maps lead prospecting tables. RLS is on with no policies, so only the
-- service-role key (used by the pipeline) can read or write.

create table if not exists maps_queries (
  id            text primary key,          -- "<category>|<area>"
  category      text not null,
  area          text not null,             -- postal code or grid cell id
  q             text not null,             -- search text sent to Maps
  ll            text,                      -- "@lat,lng,zoomz" when known
  status        text not null default 'pending',  -- pending | done | error
  result_count  integer,
  error         text,
  ran_at        timestamptz
);
create index if not exists maps_queries_status_idx on maps_queries (status);

create table if not exists maps_businesses (
  place_id          text primary key,      -- Google cid / place id
  name              text,
  clean_name        text,
  address           text,
  phone             text,
  phone_norm        text,
  website           text,
  domain            text,
  rating            real,
  review_count      integer,
  prev_review_count integer,               -- value at the previous scrape
  category          text,
  categories        jsonb,
  maps_url          text,
  lat               double precision,
  lng               double precision,
  found_by          jsonb,                 -- query ids that returned it
  first_seen        timestamptz,
  last_seen         timestamptz,
  duplicate_of      text,                  -- place_id of the kept record
  location_count    integer,
  status            text not null default 'new',  -- new | qualified | rejected | duplicate
  reject_reason     text,
  enriched_at       timestamptz,
  site_status       text,                  -- ok | dead | none
  signals           jsonb,
  socials           jsonb,
  fit_score         integer,
  intent_score      integer,
  score             integer,
  tier              text
);
create index if not exists maps_businesses_status_idx on maps_businesses (status);
create index if not exists maps_businesses_domain_idx on maps_businesses (domain);

create table if not exists maps_contacts (
  email        text primary key,           -- email-level dedupe lives here
  place_id     text not null,
  kind         text,                       -- role | named | personal
  source_url   text,
  verify       text,                       -- ok | catch_all | unknown | invalid
  also_on      jsonb,                      -- other place_ids publishing this email
  found_at     timestamptz
);
create index if not exists maps_contacts_place_idx on maps_contacts (place_id);

alter table maps_queries    enable row level security;
alter table maps_businesses enable row level security;
alter table maps_contacts   enable row level security;
