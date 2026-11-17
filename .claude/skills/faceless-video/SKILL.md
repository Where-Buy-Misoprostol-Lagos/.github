---
name: faceless-video
description: Make a finished faceless video hands-free from one topic — script, AI visuals, AI voiceover, captions, music, a long 16:9 YouTube video plus 9:16 Shorts/Reels/TikToks cut from it, and a publish kit (titles, description with chapters, tags, thumbnail). Also picks a channel niche on first run. Use when the user types /faceless-video, or asks for a faceless video, a faceless channel, or a narrated AI video without filming themselves.
argument-hint: niche | "<topic>" [--short-only | --long-only] [--minutes N] [--motion] [--hero] [--budget N]
---

# /faceless-video

One command in, one finished video set out. The user never films, records or edits.

```
/faceless-video niche                     # one-time: pick the channel's niche, style and voice
/faceless-video "why octopuses are smart" # long video (8 min) + 3 Shorts + publish kit
/faceless-video next                      # take the next topic from the backlog
/faceless-video "topic" --short-only      # one 30–50 s vertical video
/faceless-video "topic" --long-only --minutes 10
/faceless-video "topic" --hero            # add one animated AI clip as each video's opening shot
/faceless-video "topic" --motion          # premium: every scene animated (≈4x the credits)
```

## How it works (pipeline)

```
topic ─► research ─► script (beats) ─► cost check ─► images + voice (Higgsfield, parallel)
      ─► download ─► assemble.py (motion, captions, music) ─► QC ─► publish kit ─► deliver
```

Everything lives in the user's working directory under `faceless/`:

```
faceless/
  channel.md                 # niche, audience, style, voice, tone, budget: kept the same across videos
  style-key.png              # the reference image every scene is generated against (look consistency)
  topics.md                  # backlog of video ideas, used by `next`
  music/                     # optional royalty-free instrumental beds (user-supplied or generated)
  videos/<yyyy-mm-dd>-<slug>/
    script.md                # the beat script (the source of truth)
    beats.json  short1.json … # assembler manifests
    img/ vo/ clips/          # downloaded media
    out/long.mp4  out/short1.mp4 …  out/thumbnail.png
    publish.md               # titles, description + chapters, tags, hashtags, pinned comment
```

Paths in this file: `SKILL_DIR` is the folder holding this SKILL.md; the assembler is
`$SKILL_DIR/scripts/assemble.py`; templates are in `$SKILL_DIR/templates/`.

---

## Step 0 — Preflight (every run)

1. Read `faceless/channel.md`. If it is missing, run **Niche mode** first (below), then continue.
2. Check tools: `ffmpeg`, `ffprobe`, `python3` on PATH; Higgsfield tools reachable
   (load with ToolSearch `+higgsfield generate`). Call `mcp__higgsfield__balance`.
3. Read `tasks/lessons.md` if it exists and apply anything relevant.

## Niche mode (`/faceless-video niche`, or first run)

Goal: one niche the channel can make 100+ videos about, that suits AI-illustrated visuals, and
that earns well.

1. Ask the user (AskUserQuestion, one round): interests or things they know, language/market,
   any no-go topics, and monthly credit budget.
2. Build a shortlist of 8–10 candidate niches. Score each 1–5 on:
   - **Demand**: search volume and view counts. Use the DataForSEO YouTube tools
     (`serp_youtube_organic_live_advanced`, `kw_data_google_ads_search_volume`) or Semrush keyword
     tools when connected; otherwise web search. Look at what the top faceless channels in the
     niche get per video.
   - **Competition gap**: big views on small channels = gap.
   - **Ad value (RPM)**: finance, tech, business, health, education > entertainment, kids.
   - **AI-visual fit**: history, science, space, nature, psychology, mysteries, explainers and myths
     illustrate well. Avoid niches that need real footage of real people or brands.
   - **Depth**: can you list 100 distinct topics?
   - **Policy risk**: avoid medical/financial advice framing, real-person gossip, kids-directed
     content (COPPA limits), and anything that copies a single source ("reused content").
3. Present the top 3 as a table with a one-line pitch and 5 sample titles each. User picks.
4. Lock the channel: copy `templates/channel.md` to `faceless/channel.md` and fill it in:
   - **Style**: pick one non-photoreal look that fits the niche (e.g. painterly documentary,
     paper-cut diorama, bold editorial collage, moody ink illustration, clean 3D clay). Write a
     `STYLE PROMPT` suffix (medium, palette, lighting, texture, "no text, no watermark").
   - **Style key**: generate ONE 16:9 image of a typical scene with `generate_image`
     (`seedream_5_5`, `resolution: "1k"`), show it, iterate at most twice, save as
     `faceless/style-key.png` and record its `job_id` in channel.md. Every later image passes this
     job_id in `medias` with role `image_references` so the look never drifts.
   - **Voice**: `list_voices`, pick 3 that fit the tone, share their preview links, user picks.
     Record `voice_id` + `voice_type`. Never change the voice later; it is the channel's identity.
   - **Tone and pacing**: e.g. "curious friend, short sentences, one surprising fact per beat".
5. Write `faceless/topics.md`: 30 topic ideas ranked by expected interest, each with a hook line.

## Video mode

### 1. Topic and research

- Topic from the argument, or the top unchecked line of `faceless/topics.md` for `next`.
- Research with web search: gather 8–15 facts with sources. Prefer primary or reputable sources.
  Each non-obvious claim in the script must trace to a source; keep a `## Sources` list at the end
  of `script.md` (it also goes in the description). If facts conflict or can't be verified, leave
  the claim out.

### 2. Script (write `script.md` from `templates/script.md`)

The script is a list of **beats**: one beat = one spoken sentence (8–18 words, ~3–6 s) = one
image. Short beats are what keep faceless videos watchable: the picture changes every few seconds.

**Long video** (default 8 min ≈ 1,150 words ≈ 80–90 beats; `--minutes N` scales it):
- Hook (beats 1–3, under 15 s): open on the most surprising fact or a question, never "In this
  video…". Promise what the viewer gets by the end.
- 4–6 chapters, each opening with a mini-hook, each ending with an open loop to the next.
- A pattern break every ~60 s (a question to the viewer, a "but here's the problem", a number).
- Payoff, then a one-line call to action and end on a next-video tease.

**Shorts** (3 per long video, 30–50 s, 7–12 beats each):
- Each is a self-contained story pulled from the long script: pick the 3 strongest moments.
- Write a NEW first beat as the hook (first 1.5 s decides everything) and a NEW last beat
  ("Full story on the channel" or a loop line that flows back into the first beat).
- Middle beats REUSE long-video lines word for word, so their voice takes are free.

**Image prompts**: every beat gets a scene description: subject, action, setting, camera
(wide / close-up / overhead / detail), mood. Vary shot size beat to beat. No text in images, no
real logos, no real people's likenesses, no copyrighted characters. Append the channel
`STYLE PROMPT` to every prompt.

Self-check before moving on: read the hook aloud in your head — would a stranger keep watching?
Cut every beat that does not add a fact, a feeling or a turn.

### 3. Cost check (GATE)

Count what must be generated and multiply by live prices (confirm one with `get_cost: true`):

| Item | Credits (Nov 2026) |
| --- | --- |
| image, seedream_5_5 1k | 2.5 |
| voice line, seed_audio | ~0.8 |
| 10 s animated clip, minimax_h3 2K (`--hero`, `--motion`) | 20 |

Long + 3 Shorts in stills mode ≈ 90 long images + ~30 vertical images + ~96 voice lines ≈
**375 credits**. Short only ≈ **35**. `--hero` adds 20 per video; `--motion` ≈ 4x.

Show the estimate and the balance. If the estimate exceeds the balance, or the channel's
`budget_per_video` (or `--budget N`), stop and offer options: fewer minutes, shorts only, or
top up (`show_plans_and_credits`). Otherwise proceed without asking: the user chose
one-command operation.

### 4. Generate (parallel batches of 12)

- **Voice**: `generate_audio_batch`, model `seed_audio`, the locked `voice_id`/`voice_type`, one
  request per unique beat line (index = beat number). Add the channel tone as delivery direction
  if the model supports it. Shorts' new hook/outro lines are generated here too.
- **Images**: `generate_image_batch`, model `seedream_5_5`, `resolution: "1k"`, every request
  with `medias: [{value: <style key job_id>, role: "image_references"}]`.
  Long beats at `aspect_ratio: "16:9"`; Shorts beats at `"9:16"` (Shorts never reuse a cropped
  16:9 image: the crop throws away two thirds of the scene).
- **Hero clip** (`--hero`): one `minimax_h3` 10 s clip per video for beat 1, using that beat's
  image as `image_references`, aspect matching the video. Put it in the beat as `"clip"`.
- **Motion** (`--motion`): hand off to Higgsfield's built-in production pipeline instead of
  steps 4–5: `get_workflow_instructions({workflow: "faceless-video"})`, and feed it the locked
  script, style and voice from channel.md. It assembles in its own sandbox; then continue at 6.
- Poll with `jobs_wait` (≤12 jobs per call). On `nsfw` / `failed`: rewrite that prompt more
  plainly and retry once; on a second failure reuse the previous beat's image and note it.
- Download every result URL with `curl -fsSL -o` into `img/NN.png`, `vo/NN.mp3`, `clips/NN.mp4`.
  Never reuse job results across videos except the style key.

### 5. Assemble

Write manifests (see the docstring in `scripts/assemble.py`), then run:

```
python3 "$SKILL_DIR/scripts/assemble.py" faceless/videos/<slug>/beats.json   # → out/long.mp4
python3 "$SKILL_DIR/scripts/assemble.py" faceless/videos/<slug>/short1.json  # → out/short1.mp4
```

- `aspect`: `"16:9"` for long, `"9:16"` for Shorts. `captions: true` for both (most viewers
  watch muted on mobile; captions on long videos also help retention).
- `music`: a file from `faceless/music/` if present (volume 0.10–0.15; it auto-ducks under the
  voice). If none exists, ship without music and mention that adding one track improves feel.
  Only use music the user has rights to (YouTube Audio Library, their own, or AI-generated).
- The assembler times every image to its voice line, adds slow zoom/pan to stills, burns
  captions, and normalises loudness to −14 LUFS (YouTube/TikTok target).

### 6. Quality check (GATE: never deliver without it)

- `ffprobe` each output: right resolution, audio and video durations within 0.1 s.
- Long video 6–12 min (or `--minutes` ±15%); Shorts 15–59 s (must be < 60 s).
- Extract 6 frames per video (`ffmpeg -ss T -frames:v 1`) and look at them: style consistent,
  captions readable and not covering the subject, no garbled text or extra fingers in focus.
  Re-generate any broken image (one retry) and re-assemble.
- Scan the script once more for unverified claims.

### 7. Publish kit (`publish.md`, from `templates/publish.md`)

- 3 title options (≤ 60 chars, curiosity + clear subject; no clickbait the video doesn't pay off).
- Description: 2-line summary, **chapters** with timestamps computed from the beat timings
  (first chapter at 0:00, at least 3, each ≥10 s), sources, and a short AI disclosure line.
- 10–15 tags, 3–5 hashtags, a pinned comment that asks one question.
- Per Short: caption + hashtags, and which long video to link as the related video.
- **Thumbnail** (long video only): write a prompt (one bold subject, high contrast, empty space
  for 2–4 words of text) and generate it with `generate_image` 16:9 (2.5 credits). Add the
  text yourself in Canva/YouTube or ask for it to be overlaid.
- Remind the user to tick **"altered or synthetic content"** in YouTube Studio and the
  **AI-generated** label on TikTok/Instagram when scenes look realistic.

### 8. Deliver

- Send `out/long.mp4`, `out/short*.mp4`, `out/thumbnail.png` and `publish.md` to the user
  (SendUserFile when available), plus a short summary: runtime, credits spent, balance left,
  anything that needed a retry.
- Tick the topic in `topics.md`; append a row to `faceless/log.md`
  (date, topic, credits, files).
- The user posts. This skill never uploads on its own.

## Rules

- Never change the channel's style key or voice mid-channel without the user asking.
- Never spend credits beyond the confirmed estimate by more than 15% without asking.
- No real people's faces or voices, no brand logos, no copyrighted characters or music.
- Original scripts only: never rewrite a single existing video or article (platforms demonetise
  "reused content", and it is someone else's work).
- After any correction from the user, add the rule to `tasks/lessons.md`.
