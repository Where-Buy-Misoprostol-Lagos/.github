"""Stage 5: fit + intent score and an A/B/C tier for every qualified business.

Every input is something checkable from outside the company: listing data,
what the website shows, and how the review count moved between scrapes.
"""
from collections import defaultdict


def fit_score(b, contacts):
    """0-50: how reachable and established the business looks."""
    s = 0
    if b["site_status"] == "ok":
        s += 10
    usable = [c for c in contacts if c["verify"] != "invalid"]
    if usable:
        s += 15
        if any(c["kind"] == "named" for c in usable):
            s += 5
    if b["phone"]:
        s += 5
    reviews = b["review_count"] or 0
    s += 10 if reviews >= 200 else 7 if reviews >= 50 else 4 if reviews >= 10 else 0
    rating = b["rating"] or 0
    s += 5 if rating >= 4.5 else 3 if rating >= 4.0 else 0
    return min(s, 50)


def review_growth(b):
    """True when reviews rose meaningfully since the previous scrape."""
    prev, cur = b["prev_review_count"], b["review_count"] or 0
    return prev is not None and cur - prev >= max(3, prev * 0.10)


def intent_score(b, cfg):
    points, signals = cfg["score"]["points"], dict(b["signals"] or {})
    if review_growth(b):
        signals["review_growth"] = True
    weights = dict(points)
    weights.update({k["name"]: k["points"] for k in cfg["score"]["keyword_signals"]})
    return sum(w for name, w in weights.items() if signals.get(name)), signals


def score(store, cfg, log=print):
    businesses = store.select("maps_businesses", where={"status": "qualified"})
    by_place = defaultdict(list)
    for c in store.select("maps_contacts"):
        by_place[c["place_id"]].append(c)
    tiers = defaultdict(int)
    for b in businesses:
        b["fit_score"] = fit_score(b, by_place[b["place_id"]])
        b["intent_score"], b["signals"] = intent_score(b, cfg)
        b["score"] = b["fit_score"] + b["intent_score"]
        b["tier"] = ("A" if b["score"] >= cfg["score"]["tier_a"] else
                     "B" if b["score"] >= cfg["score"]["tier_b"] else "C")
        tiers[b["tier"]] += 1
    store.upsert("maps_businesses", businesses)
    log(f"{len(businesses)} scored: " + ", ".join(f"{tiers[t]} tier {t}" for t in "ABC"))
