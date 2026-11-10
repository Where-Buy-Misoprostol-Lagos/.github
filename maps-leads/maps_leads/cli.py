"""Command line entry point: python -m maps_leads <command>."""
import argparse
from collections import Counter

from . import areas, clean as clean_mod, enrich as enrich_mod, export as export_mod
from . import score as score_mod, scrape as scrape_mod
from .config import load_config, load_env
from .store import open_store


def cmd_zips(args):
    out = args.out or f"postal_{args.country.lower()}.csv"
    n = areas.download_postal_codes(args.country, out)
    print(f"Wrote {n} postal codes to {out}")


def cmd_plan(args):
    cfg = load_config(args.config)
    queries = areas.build_queries(cfg)
    print(areas.size_report(cfg, queries))
    if args.dry_run:
        return
    store = open_store()
    existing = {q["id"]: q for q in store.select("maps_queries")}
    fresh = [q for q in queries if q["id"] not in existing]
    reset = []
    if args.refresh:
        reset = [dict(existing[q["id"]], status="pending") for q in queries if q["id"] in existing]
    store.upsert("maps_queries", fresh + reset)
    print(f"Queued {len(fresh)} new queries" +
          (f", reset {len(reset)} for re-scrape" if args.refresh else
           f" ({len(queries) - len(fresh)} already in the table)"))


def cmd_stats(args):
    store = open_store()
    queries = Counter(q["status"] for q in store.select("maps_queries"))
    businesses = store.select("maps_businesses")
    contacts = store.select("maps_contacts")
    status = Counter(b["status"] for b in businesses)
    reasons = Counter(b["reject_reason"] for b in businesses if b["reject_reason"])
    qualified = [b for b in businesses if b["status"] == "qualified"]
    with_email = {c["place_id"] for c in contacts if c["verify"] != "invalid"}
    print("Queries:    " + (", ".join(f"{n} {s}" for s, n in queries.items()) or "none"))
    print(f"Businesses: {len(businesses)} unique listings")
    print(f"  duplicates removed: {status['duplicate']}")
    print(f"  rejected: {status['rejected']} " +
          (f"({', '.join(f'{n} {r}' for r, n in reasons.most_common())})" if reasons else ""))
    print(f"  qualified: {len(qualified)}")
    print(f"    enriched: {sum(1 for b in qualified if b['enriched_at'])}")
    print(f"    with email: {sum(1 for b in qualified if b['place_id'] in with_email)}")
    print(f"    with phone: {sum(1 for b in qualified if b['phone'])}")
    tiers = Counter(b["tier"] for b in qualified if b["tier"])
    print("    tiers: " + (", ".join(f"{tiers[t]} {t}" for t in "ABC") if tiers else "not scored"))
    print(f"Contacts:   {len(contacts)} unique emails " +
          f"({', '.join(f'{n} {k}' for k, n in Counter(c['kind'] for c in contacts).items())})")


def main(argv=None):
    p = argparse.ArgumentParser(prog="maps_leads", description=__doc__)
    p.add_argument("-c", "--config", default="config.toml")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("zips", help="download a country's postal codes from GeoNames")
    s.add_argument("country", help="ISO country code, e.g. US, GB, DE")
    s.add_argument("--out")
    s = sub.add_parser("plan", help="build category x area queries and show the size/cost")
    s.add_argument("--dry-run", action="store_true", help="print the size, queue nothing")
    s.add_argument("--refresh", action="store_true", help="re-queue finished queries")
    s = sub.add_parser("scrape", help="run pending queries through Serper")
    s.add_argument("--limit", type=int, help="run at most N queries (cheap test run)")
    sub.add_parser("clean", help="dedupe, clean names, qualify")
    s = sub.add_parser("enrich", help="scrape websites for emails and signals")
    s.add_argument("--limit", type=int)
    s.add_argument("--force", action="store_true", help="re-enrich everything")
    sub.add_parser("score", help="score and tier qualified businesses")
    s = sub.add_parser("export", help="write sending-ready CSVs")
    s.add_argument("--since", help="only leads first seen on/after this date (YYYY-MM-DD)")
    s = sub.add_parser("run", help="scrape, clean, enrich, score, export")
    s.add_argument("--limit", type=int, help="limit the scrape to N queries")
    sub.add_parser("stats", help="show the funnel")

    args = p.parse_args(argv)
    load_env()
    if args.cmd == "zips":
        return cmd_zips(args)
    if args.cmd == "plan":
        return cmd_plan(args)
    if args.cmd == "stats":
        return cmd_stats(args)

    cfg, store = load_config(args.config), open_store()
    if args.cmd in ("scrape", "run"):
        scrape_mod.scrape(store, cfg, limit=args.limit)
    if args.cmd in ("clean", "run"):
        clean_mod.clean(store, cfg)
    if args.cmd in ("enrich", "run"):
        enrich_mod.enrich(store, cfg, limit=getattr(args, "limit", None) if args.cmd == "enrich"
                          else None, force=getattr(args, "force", False))
    if args.cmd in ("score", "run"):
        score_mod.score(store, cfg)
    if args.cmd in ("export", "run"):
        export_mod.export(store, cfg, since=getattr(args, "since", None))
