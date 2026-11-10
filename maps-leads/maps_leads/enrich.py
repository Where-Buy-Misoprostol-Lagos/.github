"""Stage 4: read each qualified business's own website for emails and signals.

Published info@/office@ addresses reach the owner at a small business, and
they cost nothing to find. Emails are then verified and deduped at the email
level: one address published on several listings is contacted once.
"""
import html
import json
import os
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from .scrape import domain_of, is_shared_host, now

UA = "Mozilla/5.0 (compatible; maps-leads/1.0)"
EMAIL = re.compile(r"[a-z0-9][a-z0-9._%+-]{0,63}@[a-z0-9][a-z0-9.-]{0,251}\.[a-z]{2,24}", re.I)
OBFUSCATED = re.compile(r"\s*[\[({]\s*(at|dot)\s*[\])}]\s*", re.I)
CFEMAIL = re.compile(r'data-cfemail="([0-9a-f]+)"', re.I)
HREF = re.compile(r'href\s*=\s*["\']([^"\'#]+)', re.I)
CONTACT_PAGE = re.compile(r"contact|about|team|impressum|kontakt|get-in-touch|reach-us", re.I)

FREEMAIL = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "ymail.com", "hotmail.com",
    "hotmail.co.uk", "outlook.com", "live.com", "msn.com", "aol.com", "icloud.com", "me.com",
    "mac.com", "protonmail.com", "proton.me", "comcast.net", "att.net", "sbcglobal.net",
    "verizon.net", "bellsouth.net", "cox.net", "charter.net", "btinternet.com", "gmx.com",
    "mail.com", "zoho.com",
}
ROLE = {
    "info", "office", "contact", "hello", "hi", "sales", "admin", "support", "service",
    "services", "team", "enquiries", "enquiry", "inquiries", "inquiry", "mail", "email",
    "estimates", "quotes", "booking", "bookings", "help", "customerservice", "reception",
    "frontdesk", "general", "accounts", "billing", "jobs", "careers", "hr", "marketing",
}
SKIP_LOCAL = {"noreply", "no-reply", "donotreply", "do-not-reply", "abuse", "postmaster",
              "webmaster", "privacy", "dmca", "legal", "user", "name", "your", "you",
              "example", "email", "username", "yourname", "youremail", "test"}
ROLE_RANK = ["info", "office", "contact", "hello", "sales", "admin"]
ADS = re.compile(r"\bAW-\d{6,}|googleadservices\.com|googlesyndication\.com/pagead|"
                 r"fbq\(\s*['\"]init|connect\.facebook\.net/[^\"']+/fbevents", re.I)
HIRING = re.compile(r"we(?:'|’| a)re hiring|now hiring|join our team|job openings?|"
                    r"open positions?|career opportunities|apply now|/careers|/jobs\b", re.I)
SOCIAL = re.compile(r"https?://(?:www\.)?(facebook|instagram|linkedin|tiktok|youtube|houzz|"
                    r"twitter|x)\.com/[^\s\"'<>]+", re.I)


def fetch(url, timeout=10):
    """GET a page as text. Returns None on any failure or non-HTML response."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if "html" not in r.headers.get("Content-Type", "html"):
                return None
            raw = r.read(1_500_000)
            return raw.decode(r.headers.get_content_charset() or "utf-8", errors="replace")
    except Exception:
        return None


def _decode_cfemail(hexstr):
    try:
        data = bytes.fromhex(hexstr)
        return "".join(chr(b ^ data[0]) for b in data[1:])
    except ValueError:
        return ""


def classify(email):
    local, domain = email.split("@")
    if domain in FREEMAIL:
        return "personal"
    return "role" if local in ROLE else "named"


def extract_emails(page, site_domain):
    """Emails on the page that belong to this business: its own domain or a freemail box."""
    text = html.unescape(urllib.parse.unquote(page))
    text += " " + " ".join(_decode_cfemail(h) for h in CFEMAIL.findall(page))
    text = OBFUSCATED.sub(lambda m: "@" if m.group(1).lower() == "at" else ".", text)
    found = []
    for raw in EMAIL.findall(text):
        email = raw.lower().strip(".")
        local, domain = email.split("@")
        if local in SKIP_LOCAL or re.fullmatch(r"[0-9a-f]{24,}", local):
            continue
        own = domain == site_domain or domain.endswith("." + site_domain) \
            or site_domain.endswith("." + domain)
        if (own or domain in FREEMAIL) and email not in found:
            found.append(email)
    return found


def rank_emails(emails):
    """Best first: named on own domain, then info@-style, then personal boxes."""
    def key(email):
        kind, local = classify(email), email.split("@")[0]
        role_pos = ROLE_RANK.index(local) if local in ROLE_RANK else len(ROLE_RANK)
        return ({"named": 0, "role": 1, "personal": 2}[kind], role_pos, email)
    return sorted(emails, key=key)


def scan_site(business, cfg, fetch=None):
    """Fetch the homepage plus contact/about pages; return emails, signals, socials."""
    fetch = fetch or globals()["fetch"]
    e = cfg["enrich"]
    site = business["website"]
    if "//" not in site:
        site = "https://" + site
    home = fetch(site, e["timeout"])
    if home is None and site.startswith("https://"):
        site = "http://" + site[8:]
        home = fetch(site, e["timeout"])
    if home is None:
        return {"site_status": "dead", "emails": [], "signals": {}, "socials": {}}

    domain = business["domain"]
    links = []
    for href in HREF.findall(home):
        url = urllib.parse.urljoin(site, html.unescape(href))
        if url.startswith("http") and domain_of(url) == domain and CONTACT_PAGE.search(
                urllib.parse.urlsplit(url).path) and url not in links:
            links.append(url)
    if not links:
        links = [urllib.parse.urljoin(site, "/contact")]
    pages = [(site, home)]
    for url in links[:e["max_pages_per_site"] - 1]:
        body = fetch(url, e["timeout"])
        if body:
            pages.append((url, body))

    emails, sources = [], {}
    for url, body in pages:
        for email in extract_emails(body, domain):
            if email not in sources:
                sources[email] = url
                emails.append(email)

    everything = "\n".join(body for _, body in pages)
    visible = re.sub(r"<(script|style)\b.*?</\1>|<[^>]+>", " ", everything, flags=re.S | re.I)
    visible = html.unescape(visible).lower()
    signals = {}
    if ADS.search(everything):
        signals["runs_ads"] = True
    if HIRING.search(everything):
        signals["hiring"] = True
    for sig in cfg["score"]["keyword_signals"]:
        if any(k.lower() in visible for k in sig["any"]):
            signals[sig["name"]] = True
    socials = {}
    for m in SOCIAL.finditer(everything):
        socials.setdefault(m.group(1).lower(), m.group(0).rstrip("/\\"))
    return {"site_status": "ok", "emails": [(e_, sources[e_]) for e_ in rank_emails(emails)[:3]],
            "signals": signals, "socials": socials}


@lru_cache(maxsize=None)
def _has_mx(domain):
    """True/False from a DNS-over-HTTPS MX lookup, None if the lookup failed."""
    try:
        url = "https://dns.google/resolve?" + urllib.parse.urlencode({"name": domain, "type": "MX"})
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.load(r)
        return any(a.get("type") == 15 for a in data.get("Answer", []))
    except Exception:
        return None


def verify_email(email):
    """ok | catch_all | mx_ok | unknown | invalid.

    Uses MillionVerifier when MILLIONVERIFIER_API_KEY is set (mailbox-level).
    Otherwise falls back to a free MX check, which only proves the domain
    accepts mail ("mx_ok"), not that the mailbox exists.
    """
    key = os.environ.get("MILLIONVERIFIER_API_KEY")
    if key:
        try:
            url = "https://api.millionverifier.com/api/v3/?" + urllib.parse.urlencode(
                {"api": key, "email": email})
            with urllib.request.urlopen(url, timeout=30) as r:
                result = json.load(r).get("result", "")
            return {"ok": "ok", "catch_all": "catch_all", "unknown": "unknown",
                    "error": "unknown"}.get(result, "invalid")
        except Exception:
            return "unknown"
    domain = email.split("@")[1]
    if domain in FREEMAIL:
        return "mx_ok"
    return {True: "mx_ok", False: "invalid", None: "unknown"}[_has_mx(domain)]


def enrich(store, cfg, limit=None, force=False, log=print, fetch=None, verify=None):
    verify = verify or (verify_email if cfg["enrich"]["verify"] else lambda email: "unknown")
    todo = [b for b in store.select("maps_businesses", where={"status": "qualified"})
            if force or not b["enriched_at"]]
    # Biggest first, so a shared email is assigned to the most established listing.
    todo.sort(key=lambda b: (-(b["review_count"] or 0), b["place_id"]))
    if limit:
        todo = todo[:limit]
    if not todo:
        log("Nothing to enrich.")
        return

    def work(b):
        if not b["domain"] or is_shared_host(b["domain"]):
            return {"site_status": "none", "emails": [], "signals": {}, "socials": {}}
        return scan_site(b, cfg, fetch)

    with ThreadPoolExecutor(cfg["enrich"]["workers"]) as pool:
        results = list(pool.map(work, todo))

    contacts = {c["email"]: c for c in store.select("maps_contacts")}
    stamp, changed, with_email, shared = now(), {}, 0, 0
    for b, res in zip(todo, results):
        owned = 0
        signals = {k: v for k, v in res["signals"].items()}
        for email, source in res["emails"]:
            c = contacts.get(email)
            if c and c["place_id"] != b["place_id"]:
                if b["place_id"] not in (c["also_on"] or []):
                    c["also_on"] = (c["also_on"] or []) + [b["place_id"]]
                    changed[email] = c
                signals["email_owned_by"] = c["place_id"]
                shared += 1
                continue
            if not c:
                status = verify(email)
                c = contacts[email] = {"email": email, "place_id": b["place_id"],
                                       "kind": classify(email), "source_url": source,
                                       "verify": status, "also_on": [], "found_at": stamp}
                changed[email] = c
            owned += c["verify"] != "invalid"
        if owned:
            signals.pop("email_owned_by", None)
            with_email += 1
        b.update(site_status=res["site_status"], signals=signals, socials=res["socials"],
                 enriched_at=stamp)
    store.upsert("maps_contacts", list(changed.values()))
    store.upsert("maps_businesses", todo)
    dead = sum(r["site_status"] == "dead" for r in results)
    log(f"{len(todo)} sites read: {with_email} with a usable email "
        f"({with_email * 100 // len(todo)}%), {dead} dead sites, "
        f"{shared} emails already owned by another listing")
