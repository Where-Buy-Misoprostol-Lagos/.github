"""Stage 2: run every pending query through Serper's Maps endpoint.

Resumable: each query is marked done or error as it finishes, so re-running
picks up where it stopped. Re-scrapes merge into existing businesses instead
of replacing them, keeping first_seen and the previous review count.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

PAGE_SIZE = 20

# Hosts that many unrelated businesses share; never dedupe or chain-count on them.
SHARED_HOSTS = {
    "facebook.com", "instagram.com", "linktr.ee", "wixsite.com", "business.site",
    "sites.google.com", "google.com", "yelp.com", "twitter.com", "x.com", "tiktok.com",
    "linkedin.com", "youtube.com", "wa.me", "whatsapp.com", "godaddysites.com",
    "squarespace.com", "weebly.com", "wordpress.com", "blogspot.com", "carrd.co",
    "bit.ly", "square.site", "shopify.com", "myshopify.com", "booksy.com", "fresha.com",
    "vagaro.com", "jiji.ng", "jumia.com.ng",
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def domain_of(url):
    if not url:
        return None
    host = urllib.parse.urlsplit(url if "//" in url else "//" + url).hostname or ""
    host = host.lower().removeprefix("www.")
    return host or None


def is_shared_host(domain):
    return any(domain == h or domain.endswith("." + h) for h in SHARED_HOSTS)


def norm_phone(phone):
    digits = re.sub(r"\D", "", phone or "")
    return digits[-10:] if len(digits) >= 7 else None


class SerperMaps:
    def __init__(self, api_key, country="us", language="en", base_url=None):
        self.api_key = api_key
        self.country, self.language = country, language
        self.url = (base_url or os.environ.get("SERPER_BASE_URL")
                    or "https://google.serper.dev").rstrip("/") + "/maps"

    def search(self, q, ll=None, page=1):
        body = {"q": q, "gl": self.country, "hl": self.language}
        if ll:
            body["ll"] = ll
        if page > 1:
            body["page"] = page
        req = urllib.request.Request(
            self.url, data=json.dumps(body).encode(),
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r).get("places", [])


def place_to_row(p):
    place_id = str(p.get("cid") or p.get("placeId") or p.get("fid") or "")
    if not place_id:
        return None
    website = p.get("website")
    cid = p.get("cid")
    return {
        "place_id": place_id,
        "name": p.get("title"),
        "address": p.get("address"),
        "phone": p.get("phoneNumber"),
        "phone_norm": norm_phone(p.get("phoneNumber")),
        "website": website,
        "domain": domain_of(website),
        "rating": p.get("rating"),
        "review_count": p.get("ratingCount") or 0,
        "category": p.get("type"),
        "categories": p.get("types") or ([p["type"]] if p.get("type") else []),
        "maps_url": (f"https://www.google.com/maps?cid={cid}" if cid else
                     f"https://www.google.com/maps/place/?q=place_id:{place_id}"),
        "lat": p.get("latitude"),
        "lng": p.get("longitude"),
    }


def run_query(client, query, max_pages):
    """All result pages for one query. Stops at the first short or repeated page."""
    places, seen = [], set()
    for page in range(1, max_pages + 1):
        try:
            batch = client.search(query["q"], query["ll"], page)
        except urllib.error.HTTPError:
            if page == 1:
                raise
            break  # deeper pages are best effort
        fresh = [p for p in (place_to_row(x) for x in batch) if p and p["place_id"] not in seen]
        seen.update(p["place_id"] for p in fresh)
        places += fresh
        if len(batch) < PAGE_SIZE or not fresh:
            break
    return places


def merge_places(store, places, query_id, stamp):
    """Upsert scraped places, preserving everything later stages wrote."""
    existing = {b["place_id"]: b for b in store.select(
        "maps_businesses", in_=("place_id", [p["place_id"] for p in places]))}
    rows = []
    for p in places:
        old = existing.get(p["place_id"])
        if old:
            row = dict(old)
            if (old["last_seen"] or "")[:10] != stamp[:10]:
                row["prev_review_count"] = old["review_count"]
            row.update(p)
            row["found_by"] = sorted(set(old["found_by"] or []) | {query_id})
        else:
            row = dict(p, first_seen=stamp, found_by=[query_id], status="new")
        row["last_seen"] = stamp
        rows.append(row)
    store.upsert("maps_businesses", rows)
    return sum(1 for p in places if p["place_id"] not in existing)


def scrape(store, cfg, limit=None, log=print):
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        raise SystemExit("SERPER_API_KEY is not set (get one at serper.dev, put it in .env)")
    client = SerperMaps(key, cfg["market"]["country"], cfg["market"]["language"])
    pending = store.select("maps_queries", where={"status": "pending"})
    pending += store.select("maps_queries", where={"status": "error"})
    if limit:
        pending = pending[:limit]
    if not pending:
        log("No pending queries. Run `plan` first, or `plan --refresh` to re-scrape.")
        return
    stamp, done, new_total, errors = now(), 0, 0, 0
    with ThreadPoolExecutor(cfg["scrape"]["workers"]) as pool:
        futures = {pool.submit(run_query, client, q, cfg["scrape"]["max_pages"]): q
                   for q in pending}
        for fut in as_completed(futures):
            q = futures[fut]
            try:
                places = fut.result()
                new_total += merge_places(store, places, q["id"], stamp)
                q.update(status="done", result_count=len(places), error=None, ran_at=now())
            except Exception as e:  # one bad query must not stop the run
                errors += 1
                q.update(status="error", error=str(e)[:300], ran_at=now())
            store.upsert("maps_queries", [q])
            done += 1
            if done % 50 == 0 or done == len(pending):
                log(f"  {done}/{len(pending)} queries, {new_total} new businesses, {errors} errors")
    if errors:
        log(f"{errors} queries failed; run `scrape` again to retry them.")
