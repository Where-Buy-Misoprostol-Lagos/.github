"""Unit tests plus an end-to-end run against a fake Serper API and fake websites."""
import csv
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from maps_leads import areas, clean, enrich, export, score, scrape
from maps_leads.config import DEFAULTS, _merge
from maps_leads.store import SQLiteStore, SupabaseStore


def place(cid, title, phone=None, website=None, reviews=50, rating=4.6,
          address="1 Main St, Dallas, TX 75201", type_="Roofing contractor"):
    return {"cid": str(cid), "title": title, "address": address, "phoneNumber": phone,
            "website": website, "ratingCount": reviews, "rating": rating, "type": type_,
            "latitude": 32.78, "longitude": -96.8}


BEST = place(1, "BEST ROOFING DALLAS TX - Free Estimates", "(214) 555-0001",
             "https://bestroofing.com", reviews=120)
FILLER = [place(1000 + i, f"Filler Roofing {i}", f"(214) 556-{i:04d}",
                f"https://filler{i}.com", reviews=3) for i in range(24)]
RESULTS = {
    # 75201: page 1 is a full page of 20, page 2 has the rest.
    ("roofer 75201", 1): [BEST] + FILLER[:19],
    ("roofer 75201", 2): FILLER[19:],
    ("roofer 75202", 1): [
        BEST,  # same listing again: zip codes overlap
        place(2, "Apex Roofing LLC", "214-555-0002", "https://apexroofing.com", reviews=80),
        place(3, "Apex Roofing - North Office", "+1 214 555 0002", None, reviews=5),  # same phone
        place(4, "Solo Roofer", "214-555-0004", None, reviews=40),                    # no site
        place(5, "Tiny Roofing", "214-555-0005", "https://tinyroofing.com", reviews=2),
        place(6, "Joe's Roofs", "214-555-0006", "https://joesroofs.com", reviews=30),
        place(7, "Joe's Gutters", "214-555-0007", "https://joesgutters.com", reviews=20),
        place(8, "Ghost Roofing", "214-555-0008", "https://ghostroofing.com", reviews=15),
        place(9, "Social Only Roofing", "214-555-0009", "https://facebook.com/social", reviews=60),
    ] + [place(20 + i, f"MegaRoof #{i}", f"214-555-01{i:02d}", "https://megaroof.com/loc",
               reviews=300) for i in range(4)],
    ("roofing contractor 75201", 1): [BEST],
    ("roofing contractor 75202", 1): [],
}
SITES = {
    "https://bestroofing.com": '<a href="/contact-us">Contact</a> <a href="/careers">We\'re hiring</a>'
                               "<script>gtag('config','AW-123456789')</script>"
                               '<a href="https://www.facebook.com/bestroofing">fb</a>',
    "https://bestroofing.com/contact-us": 'Mail <a href="mailto:info@bestroofing.com?subject=x">us</a>'
                                          " or mike@bestroofing.com. We do commercial roofing."
                                          " Site by hello@webagency.io <img src='logo@2x.png'>",
    "https://apexroofing.com": "Write to office [at] apexroofing [dot] com",
    "https://joesroofs.com": "joe.the.roofer@gmail.com",
    "https://joesgutters.com": "Email: joe.the.roofer@gmail.com",
    # ghostroofing.com is absent: dead site
}


class FakeSerper(BaseHTTPRequestHandler):
    calls = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeSerper.calls.append(body)
        assert self.headers["X-API-KEY"] == "test-key"
        places = RESULTS.get((body["q"], body.get("page", 1)), [])
        data = json.dumps({"places": places}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def make_cfg(tmp):
    zips = os.path.join(tmp, "zips.csv")
    with open(zips, "w") as f:
        f.write("zip,state,lat,lng\n75201,TX,32.78,-96.80\n75202,TX,32.77,-96.81\n"
                "10001,NY,40.75,-73.99\n")
    return _merge(DEFAULTS, {
        "market": {"categories": ["roofer", "roofing contractor"]},
        "areas": {"mode": "postal", "file": zips, "regions": ["TX"]},
        "qualify": {"category_keywords": ["roof"]},
        "score": {"keyword_signals": [{"name": "commercial", "points": 6,
                                       "any": ["commercial roofing"]}]},
        "export": {"dir": os.path.join(tmp, "exports")},
    })


class UnitTests(unittest.TestCase):
    def test_clean_name(self):
        cases = {
            ("BEST ROOFING DALLAS TX - Free Estimates", "1 Main St, Dallas, TX 75201"): "Best Roofing",
            ("Apex Roofing LLC", None): "Apex Roofing",
            ("JD HVAC & PLUMBING, INC.", None): "JD HVAC & Plumbing",
            ("Roofers of Dallas", "1 Main St, Dallas, TX 75201"): "Roofers of Dallas",
            ("Smith, Jones & Sons Roofing", None): "Smith, Jones & Sons Roofing",
            ("joe's roofing | 24/7 emergency", None): "Joe's Roofing",
            ("O'Brien Dental (Downtown)", None): "O'Brien Dental",
        }
        for (name, addr), want in cases.items():
            self.assertEqual(clean.clean_name(name, addr), want)

    def test_extract_emails_keeps_only_the_business(self):
        page = ('<a href="mailto:Info@Acme.com">x</a> sales(at)acme(dot)com owner@gmail.com '
                'dev@agency.io noreply@acme.com img@2x.png '
                '<a data-cfemail="7e171018113e1f1d131b501d1113">[email&#160;protected]</a>')
        self.assertEqual(sorted(enrich.extract_emails(page, "acme.com")),
                         ["info@acme.com", "owner@gmail.com", "sales@acme.com"])

    def test_rank_emails(self):
        self.assertEqual(enrich.rank_emails(["x@gmail.com", "sales@a.com", "info@a.com", "bob@a.com"]),
                         ["bob@a.com", "info@a.com", "sales@a.com", "x@gmail.com"])

    def test_grid_covers_bbox(self):
        cells = areas.grid_areas([6.40, 3.30, 6.50, 3.40], 3.0)
        self.assertEqual(len(cells), 16)  # ~11km x 11km box in 3km cells
        self.assertTrue(all(6.40 <= c["lat"] <= 6.53 and 3.30 <= c["lng"] <= 3.43 for c in cells))
        cfg = _merge(DEFAULTS, {"market": {"categories": ["pharmacy"]},
                                "areas": {"mode": "grid", "bbox": [6.40, 3.30, 6.50, 3.40]}})
        q = areas.build_queries(cfg)[0]
        self.assertEqual(q["q"], "pharmacy")
        self.assertRegex(q["ll"], r"^@6\.\d+,3\.\d+,13z$")

    def test_phone_and_domain(self):
        self.assertEqual(scrape.norm_phone("+1 (214) 555-0002"), scrape.norm_phone("214-555-0002"))
        self.assertEqual(scrape.domain_of("https://www.Acme.com/x?y"), "acme.com")
        self.assertTrue(scrape.is_shared_host("m.facebook.com"))

    def test_supabase_requests(self):
        sent = []
        s = SupabaseStore("https://x.supabase.co", "k")
        s._request = lambda method, path, body=None, prefer=None: sent.append(
            (method, path, body, prefer)) or []
        s.upsert("maps_contacts", [{"email": "a@b.c", "place_id": "1"}])
        s.select("maps_businesses", where={"status": "qualified"}, in_=("place_id", ["1", "2"]))
        self.assertEqual(sent[0][:2], ("POST", "maps_contacts?on_conflict=email"))
        self.assertEqual(set(sent[0][2][0]), {"email", "place_id", "kind", "source_url",
                                              "verify", "also_on", "found_at"})
        self.assertIn("merge-duplicates", sent[0][3])
        self.assertIn("status=eq.qualified", sent[1][1])
        self.assertIn("place_id=in.%28%221%22%2C%222%22%29", sent[1][1])


class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeSerper)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        os.environ.update(SERPER_API_KEY="test-key", no_proxy="127.0.0.1", NO_PROXY="127.0.0.1",
                          SERPER_BASE_URL=f"http://127.0.0.1:{cls.server.server_port}")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_full_pipeline(self):
        tmp = tempfile.mkdtemp()
        cfg = make_cfg(tmp)
        store = SQLiteStore(os.path.join(tmp, "t.db"))
        quiet = lambda *a: None
        fetch = lambda url, timeout=10: SITES.get(url.rstrip("/"))
        verify = lambda email: "ok"

        # Stage 1: 2 categories x 2 Texas zips (NY filtered out)
        queries = areas.build_queries(cfg)
        self.assertEqual(len(queries), 4)
        self.assertIn("4 queries", areas.size_report(cfg, queries))
        store.upsert("maps_queries", queries)

        # Stage 2
        FakeSerper.calls.clear()
        scrape.scrape(store, cfg, log=quiet)
        self.assertEqual({q["status"] for q in store.select("maps_queries")}, {"done"})
        self.assertEqual(len(FakeSerper.calls), 5)  # 4 queries + 1 second page
        self.assertEqual(FakeSerper.calls[0]["gl"], "us")
        biz = {b["place_id"]: b for b in store.select("maps_businesses")}
        self.assertEqual(len(biz), 1 + 24 + 8 + 4)  # BEST seen 3 times, stored once
        self.assertEqual(len(biz["1"]["found_by"]), 3)

        # Stage 3
        clean.clean(store, cfg, log=quiet)
        biz = {b["place_id"]: b for b in store.select("maps_businesses")}
        self.assertEqual(biz["1"]["clean_name"], "Best Roofing")
        self.assertEqual((biz["3"]["status"], biz["3"]["duplicate_of"]), ("duplicate", "2"))
        self.assertEqual(biz["4"]["reject_reason"], "no_website")
        self.assertEqual(biz["5"]["reject_reason"], "too_few_reviews")
        self.assertEqual(biz["9"]["reject_reason"], "no_website")  # social page is not a site
        mega = [biz[str(20 + i)] for i in range(4)]
        self.assertEqual(sorted(b["status"] for b in mega), ["duplicate"] * 3 + ["rejected"])
        self.assertEqual({b["reject_reason"] for b in mega if b["status"] == "rejected"}, {"chain"})
        qualified = sorted(p for p, b in biz.items() if b["status"] == "qualified")
        self.assertEqual(qualified, ["1", "2", "6", "7", "8"])

        # Stage 4
        enrich.enrich(store, cfg, log=quiet, fetch=fetch, verify=verify)
        contacts = {c["email"]: c for c in store.select("maps_contacts")}
        self.assertEqual(sorted(contacts), ["info@bestroofing.com", "joe.the.roofer@gmail.com",
                                            "mike@bestroofing.com", "office@apexroofing.com"])
        joe = contacts["joe.the.roofer@gmail.com"]
        self.assertEqual((joe["place_id"], joe["also_on"], joe["kind"]), ("6", ["7"], "personal"))
        biz = {b["place_id"]: b for b in store.select("maps_businesses")}
        self.assertEqual(biz["8"]["site_status"], "dead")
        self.assertEqual(biz["7"]["signals"], {"email_owned_by": "6"})
        self.assertEqual(biz["1"]["signals"], {"runs_ads": True, "hiring": True, "commercial": True})
        self.assertIn("facebook", biz["1"]["socials"])

        # Stage 5
        score.score(store, cfg, log=quiet)
        biz = {b["place_id"]: b for b in store.select("maps_businesses")}
        self.assertEqual((biz["1"]["fit_score"], biz["1"]["intent_score"], biz["1"]["tier"]),
                         (47, 22, "A"))
        self.assertEqual(biz["2"]["tier"], "B")
        self.assertEqual(biz["8"]["tier"], "C")

        # Export
        export.export(store, cfg, log=quiet)
        def read(name):
            with open(os.path.join(cfg["export"]["dir"], name)) as f:
                return list(csv.DictReader(f))
        business, personal, calls = (read("emails_business.csv"), read("emails_personal.csv"),
                                     read("call_list.csv"))
        self.assertEqual([r["email"] for r in business],
                         ["mike@bestroofing.com", "office@apexroofing.com"])
        self.assertEqual(business[0]["other_emails"], "info@bestroofing.com")
        self.assertEqual([r["email"] for r in personal], ["joe.the.roofer@gmail.com"])
        self.assertEqual([r["company"] for r in calls],
                         ["Best Roofing", "Apex Roofing", "Joe's Roofs", "Ghost Roofing"])

        # Re-scrape: resumable, idempotent, and review growth becomes a signal
        enrich.enrich(store, cfg, log=quiet, fetch=fetch, verify=verify)  # nothing left to do
        for q in store.select("maps_queries"):
            store.upsert("maps_queries", [dict(q, status="pending")])
        b = biz["2"]
        store.upsert("maps_businesses", [dict(b, last_seen="2026-01-01T00:00:00+00:00",
                                              review_count=60)])
        scrape.scrape(store, cfg, log=quiet)
        clean.clean(store, cfg, log=quiet)
        score.score(store, cfg, log=quiet)
        after = {b["place_id"]: b for b in store.select("maps_businesses")}
        self.assertEqual(len(after), len(biz))
        self.assertEqual(after["2"]["prev_review_count"], 60)
        self.assertTrue(after["2"]["signals"]["review_growth"])
        self.assertEqual(after["2"]["first_seen"], biz["2"]["first_seen"])
        self.assertTrue(after["1"]["enriched_at"])  # enrichment survived the re-scrape
        self.assertEqual(len(store.select("maps_contacts")), 4)


if __name__ == "__main__":
    unittest.main()
