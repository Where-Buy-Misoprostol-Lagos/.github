# Faceless video skill: setup

Type one command with a topic, get a finished faceless video: an 8-minute YouTube video, 3 Shorts
cut from it, captions, AI voice, AI visuals and a ready-to-paste publish kit. You never film,
record or edit.

## What you need (one time, ~15 minutes)

| # | Thing | Why | Cost |
| --- | --- | --- | --- |
| 1 | **Claude Code** (CLI, desktop app or claude.ai/code) | runs the skill | your Claude plan |
| 2 | **Higgsfield connector** in claude.ai → Settings → Connectors | AI images, AI voice, optional AI clips | credits (see below) |
| 3 | **ffmpeg** (`brew install ffmpeg` / `sudo apt install ffmpeg` / `winget install ffmpeg`) | assembles the video locally, free | free |
| 4 | **Python 3** | runs `scripts/assemble.py` | free |
| 5 | Optional: **DataForSEO** or **Semrush** connector | real search/YouTube demand data for picking a niche | per their plan |
| 6 | Optional: royalty-free music in `faceless/music/` (YouTube Audio Library) | background bed, auto-ducked under the voice | free |
| 7 | YouTube channel + TikTok/Instagram accounts | where you post | free |

Cloud sessions on claude.ai/code already have ffmpeg and Python, so only the Higgsfield
connector is needed there.

## Install the skill

The skill lives in this repo at `.claude/skills/faceless-video/`.

- **Use it from this repo:** open Claude Code in this repository; `/faceless-video` is available.
- **Use it everywhere:** copy the folder to your personal skills:
  `cp -r .claude/skills/faceless-video ~/.claude/skills/`

## Credits (Higgsfield, live prices Nov 2026)

| Video | Default (AI stills + free local motion) | `--hero` | `--motion` (all AI clips) |
| --- | --- | --- | --- |
| One 45 s Short | ~35 credits | +20 | ~110 |
| 8 min video + 3 Shorts | ~375 credits | +80 | ~1,300 |

The free plan's 10 credits are not enough for one Short; top up or start a plan first
(ask Claude: "show Higgsfield plans").

## Daily use

```
/faceless-video niche                 # first time only: picks niche, look, voice, 30 topic ideas
/faceless-video next                  # makes the next video from your topic list
/faceless-video "how ancient Rome built roads that still exist"
/faceless-video "topic" --short-only  # just one vertical video
```

You get `faceless/videos/<date>-<topic>/out/` with `long.mp4`, `short1-3.mp4`,
`thumbnail.png` and `publish.md`. Review, paste the title/description, tick the AI-content label,
post.

## Suggested weekly rhythm

- 1 long video + 3 Shorts per week at ~375 credits (≈1,500 credits/month), or
- Shorts only: 1 per day at ~35 credits (≈1,050 credits/month).
- Post Shorts on days the long video isn't out; link each Short to the long video.
