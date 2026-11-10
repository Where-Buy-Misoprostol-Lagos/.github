"""Export sending-ready CSVs, one per channel.

emails_business.csv  addresses on the company's own domain (main sending account)
emails_personal.csv  Gmail/Yahoo-style addresses (send from a separate account)
call_list.csv        every lead with a phone number, best tier first
all_leads.csv        everything, for your CRM
"""
import csv
import os
from collections import defaultdict

from .enrich import rank_emails

COLUMNS = ["tier", "score", "fit_score", "intent_score", "company", "first_name", "email",
           "email_kind", "email_verify", "other_emails", "phone", "website", "address",
           "category", "rating", "review_count", "signals", "first_seen", "maps_url", "place_id"]


def build_rows(store):
    by_place = defaultdict(dict)
    for c in store.select("maps_contacts"):
        if c["verify"] != "invalid":
            by_place[c["place_id"]][c["email"]] = c
    rows = []
    for b in store.select("maps_businesses", where={"status": "qualified"}):
        signals = b["signals"] or {}
        if signals.get("email_owned_by"):
            continue  # same owner is already reached through another listing
        contacts = by_place[b["place_id"]]
        ranked = rank_emails(list(contacts))
        best = contacts[ranked[0]] if ranked else None
        rows.append({
            "tier": b["tier"], "score": b["score"], "fit_score": b["fit_score"],
            "intent_score": b["intent_score"], "company": b["clean_name"] or b["name"],
            "first_name": "",  # website emails have no named person; open without one
            "email": best["email"] if best else "",
            "email_kind": best["kind"] if best else "",
            "email_verify": best["verify"] if best else "",
            "other_emails": ";".join(ranked[1:]),
            "phone": b["phone"] or "", "website": b["website"] or "",
            "address": b["address"] or "", "category": b["category"] or "",
            "rating": b["rating"], "review_count": b["review_count"],
            "signals": ";".join(sorted(k for k, v in signals.items() if v is True)),
            "first_seen": b["first_seen"], "maps_url": b["maps_url"], "place_id": b["place_id"],
        })
    rows.sort(key=lambda r: (r["tier"] or "Z", -(r["score"] or 0), r["company"] or ""))
    return rows


def export(store, cfg, since=None, log=print):
    rows = build_rows(store)
    if since:
        rows = [r for r in rows if (r["first_seen"] or "") >= since]
    out_dir = cfg["export"]["dir"]
    os.makedirs(out_dir, exist_ok=True)
    files = {
        "emails_business.csv": [r for r in rows if r["email"] and r["email_kind"] != "personal"],
        "emails_personal.csv": [r for r in rows if r["email_kind"] == "personal"],
        "call_list.csv": [r for r in rows if r["phone"]],
        "all_leads.csv": rows,
    }
    for name, subset in files.items():
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(subset)
        log(f"  {out_dir}/{name}: {len(subset)} leads")
