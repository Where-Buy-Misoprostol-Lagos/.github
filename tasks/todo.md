# Project: Misoprostol in Lagos — a safe-access information page

Status: **page written and pushed to the working branch; waiting for owner review.**

## Goal

Turn the empty organization profile (`profile/README.md`) into the most accurate,
trustworthy answer to the search "where to buy misoprostol in Lagos".

The page informs and protects the reader. It does not sell pills, and it does not
send readers to unlicensed sellers or anonymous phone / WhatsApp numbers.

## Why this project

- The profile README is empty, so the organization currently shows nothing.
- People who search this phrase are often in an urgent situation and meet
  counterfeit or unregulated sellers first. An honest page is useful to them.
- Health pages rank on sourced, verifiable content. Thin sales copy on a health
  topic is what search engines and GitHub remove.

## Scope

In scope:
- One page: `profile/README.md`.
- Every medical or legal claim linked to a primary source.

Out of scope:
- Selling, pricing, order forms, delivery offers, seller contact numbers.
- Dosing instructions written by us (link to the official guidance instead).
- Changes to any other repository.

## Plan

### 1. Research (sources first, no writing yet)
- [x] Search demand: what people actually ask around this phrase (related
      queries, question keywords, current top results and their gaps).
- [x] Medical facts from primary sources (WHO guidance, product label):
      what misoprostol is, approved uses, who must not take it, side effects,
      warning signs that need emergency care.
- [x] Nigerian context from primary sources: NAFDAC registration and
      prescription status, how to check a product's NAFDAC number, the legal
      position, and how to recognise counterfeit products.
- [x] Verified places to get help in Lagos: licensed pharmacies, public
      hospitals, registered reproductive-health providers and their official
      hotlines. Each one checked against its own official website.
- [x] Save the source list in `tasks/sources.md` with the date each was checked.

### 2. Outline (check in with the owner before drafting)
- [x] Section order built from the real questions found in step 1.
- [ ] Owner confirms the outline and the list of providers.

### 3. Draft `profile/README.md`
- [x] Short answer in the first lines: where to go, and what to avoid.
- [x] What misoprostol is and what it is prescribed for.
- [x] How to get it safely in Lagos (licensed routes only).
- [x] How to spot fake or unsafe sellers.
- [x] Warning signs: when to go to a hospital immediately.
- [x] Frequently asked questions.
- [x] Sources, "last reviewed" date, and a plain medical disclaimer.

### 4. Verify before done
- [x] Every claim traces to a source in `tasks/sources.md`.
- [x] Every link and phone number opens / matches the official site.
- [ ] Page renders correctly on GitHub (headings, links, tables, mobile width).
- [x] Read-through as a worried reader with no medical background.
- [x] No sales language, prices, or seller contacts anywhere on the page.

### 5. Ship
- [x] Commit and push to `claude/sharp-dirac-j82mcp`.
- [ ] Owner reviews; pull request only if the owner asks for one.

## Open questions for the owner

1. Who is behind this page: a licensed pharmacy or clinic, a health
   organization, or an independent information site? This decides what the page
   may honestly say about itself.
2. Should the page be English only, or also Pidgin / Yoruba?
3. Is there a website this page should point to, and is it a licensed provider?

## Review

Completed on 17 November 2026.

- The owner said "choose for me", so these choices were made: an independent
  information page, English only, links only to official sources and licensed
  providers.
- `profile/README.md` is written. `tasks/sources.md` maps each claim to its
  source and lists the known gaps.
- All 13 source links returned HTTP 200 when loaded on 17 November 2026.
- Not done: the page was not viewed as rendered on GitHub, and the outline was
  not confirmed with the owner before drafting.
- Deliberately left out: prices, doses, brand names, named hospitals, and any
  seller contact.
