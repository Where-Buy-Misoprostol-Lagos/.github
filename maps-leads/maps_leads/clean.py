"""Stage 3: business-level dedupe, name cleaning, chain filter, qualification.

Runs before enrichment so no lookup is spent on a business that gets cut.
Recomputes every row from scratch, so it is safe to re-run after each scrape.
"""
import re
from collections import defaultdict

from .scrape import is_shared_host

SEPARATORS = re.compile(r"\s+[-–—•·]\s+|\s*[|(\[]\s*|:\s+")
LEGAL = re.compile(r"[,\s]+(l\.?l\.?c|inc|ltd|limited|corp|co|pllc|llp|plc|gmbh)\.?$", re.I)
ACRONYMS = {"HVAC", "AC", "A/C", "USA", "UK", "DJ", "BBQ", "IT", "TV", "RV", "ATV", "CPA", "DDS",
            "MD", "PC", "II", "III", "IV", "NYC", "DFW", "LA"}
SMALL = {"and", "of", "the", "in", "at", "for", "by", "on", "to", "a", "an", "&"}
LINKING = {"of", "in", "at", "for", "by", "on", "to", "&", "and", "the"}


def _title_word(word, first):
    bare = re.sub(r"[^A-Za-z/]", "", word)
    if bare.upper() in ACRONYMS or re.search(r"\d", word):
        return word.upper()
    if len(bare) <= 3 and bare and not re.search(r"[AEIOUYaeiouy]", bare):
        return word.upper()  # vowel-less short tokens are almost always initials
    if word.lower() in SMALL and not first:
        return word.lower()
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda m: m.group(0).capitalize(), word)


def clean_name(name, address=None):
    """'BEST ROOFING DALLAS TX - Free Estimates' -> 'Best Roofing'."""
    if not name:
        return name
    out = re.sub(r"\s+", " ", name).strip()
    head = SEPARATORS.split(out, maxsplit=1)[0].strip()
    if len(head) >= 3:
        out = head
    while LEGAL.search(out):
        out = LEGAL.sub("", out).strip()

    # Drop a location tacked on the end ("... Dallas TX"), using the listing's own address.
    place_words = set()
    if address:
        parts = [p.strip() for p in address.split(",")]
        for part in parts[1:]:
            place_words.update(w.lower() for w in re.findall(r"[A-Za-z]+", part))
    words = out.split()
    while len(words) > 2 and words[-1].lower().strip(".,") in place_words \
            and words[-2].lower() not in LINKING:
        words.pop()
    out = " ".join(words).strip(" ,-")

    letters = re.sub(r"[^A-Za-z]", "", out)
    if letters and (letters.isupper() or letters.islower()):
        out = " ".join(_title_word(w, i == 0) for i, w in enumerate(out.split()))
    return out or name


def dedupe(businesses):
    """Group listings that share a phone or a website domain.

    The listing with the most reviews is kept; the rest are marked duplicate.
    The group size becomes location_count, which the chain filter uses.
    (Same-place_id repeats from overlapping areas were already merged on write.)
    """
    parent = {b["place_id"]: b["place_id"] for b in businesses}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_key = {}
    for b in businesses:
        keys = []
        if b["phone_norm"]:
            keys.append(("phone", b["phone_norm"]))
        if b["domain"] and not is_shared_host(b["domain"]):
            keys.append(("domain", b["domain"]))
        for key in keys:
            if key in by_key:
                parent[find(b["place_id"])] = find(by_key[key])
            else:
                by_key[key] = b["place_id"]

    groups = defaultdict(list)
    for b in businesses:
        groups[find(b["place_id"])].append(b)
    for group in groups.values():
        group.sort(key=lambda b: (-(b["review_count"] or 0), b["place_id"]))
        keep = group[0]
        keep["duplicate_of"], keep["location_count"] = None, len(group)
        for dup in group[1:]:
            dup["duplicate_of"], dup["location_count"] = keep["place_id"], len(group)


def reject_reason(b, q):
    """Why a business fails the ICP filters, or None if it qualifies."""
    has_site = bool(b["domain"]) and not is_shared_host(b["domain"])
    if q["require_website"] and not has_site:
        return "no_website"
    if (b["review_count"] or 0) < q["min_reviews"]:
        return "too_few_reviews"
    rating = b["rating"]
    if rating is None:
        if q["min_rating"] > 0:
            return "no_rating"
    elif not q["min_rating"] <= rating <= q["max_rating"]:
        return "rating_out_of_range"
    cats = " | ".join([b["category"] or ""] + (b["categories"] or [])).lower()
    if q["category_keywords"] and not any(k.lower() in cats for k in q["category_keywords"]):
        return "wrong_category"
    name = (b["name"] or "").lower()
    if any(k.lower() in name for k in q["exclude_name_keywords"]):
        return "excluded_name"
    locations = b["location_count"] or 1
    if q["max_locations"] and locations > q["max_locations"]:
        return "chain"
    if locations < q.get("min_locations", 1):
        return "too_few_locations"
    return None


def clean(store, cfg, log=print):
    businesses = store.select("maps_businesses")
    dedupe(businesses)
    counts = defaultdict(int)
    for b in businesses:
        b["clean_name"] = clean_name(b["name"], b["address"])
        if b["duplicate_of"]:
            b["status"], b["reject_reason"] = "duplicate", None
        else:
            reason = reject_reason(b, cfg["qualify"])
            b["status"], b["reject_reason"] = ("rejected", reason) if reason else ("qualified", None)
        counts[b["reject_reason"] or b["status"]] += 1
    store.upsert("maps_businesses", businesses)
    log(f"{len(businesses)} businesses: " +
        ", ".join(f"{n} {k}" for k, n in sorted(counts.items(), key=lambda x: -x[1])))
