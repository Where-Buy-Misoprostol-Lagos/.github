# Faceless video system — plan

Goal: type one command with a topic, get a finished faceless video (long 16:9 + shorts 9:16)
plus its title, description, hashtags and thumbnail prompt. No camera, no mic, no editing.

Decisions (from the user): format = BOTH (one long video, cut into shorts) · visuals = AI-generated
scenes (Higgsfield) · automation = one command per video, user reviews and posts · niche = not yet
chosen, so the skill starts with a niche-picking step.

## Cost reality (Higgsfield live prices, checked 2026-11-17)

| Item | Credits |
| --- | --- |
| AI image (seedream 5.5, 1k) | 2.5 |
| Voice line (~8 s, seed_audio) | 0.8 |
| Animated clip, 10 s (minimax h3, 2K) | 20 |

| Video | STILLS mode (images + local motion) | MOTION mode (all AI clips) |
| --- | --- | --- |
| 45 s short (~10 beats) | ~35 | ~110 |
| 8 min long (~90 beats) | ~300 | ~1,000+ |
| 8 min long + 3 shorts (shorts reuse voice) | ~375 | ~1,300 |

The account currently has 10 credits (free plan), so the default is STILLS mode with free local
motion (slow zoom/pan done by ffmpeg) and optional "hero" AI clips only for the first 3 seconds.

## Build checklist

- [x] Ask format / visuals / automation / niche
- [x] Read Higgsfield's built-in `faceless-video` workflow and get live prices
- [x] `.claude/skills/faceless-video/SKILL.md`: the `/faceless-video` command
- [x] `channel.md` template: niche, style, voice, tone, kept the same across all videos
- [x] Script template: hook, retention beats, chapters, 3 shorts
- [x] `scripts/assemble.py`: images + voice lines → MP4 with motion, captions, music, 16:9 or 9:16
- [x] Test the assembler end-to-end with dummy media (both ratios)
- [x] Commit and push to `claude/dreamy-tesla-9yee5u`
- [ ] User: buy credits / start a plan on Higgsfield (needed before the first real video)
- [ ] User: run `/faceless-video niche` once, then `/faceless-video "<topic>"`

## Review

- Assembler tested with dummy images/tones/clip/music in 16:9 and 9:16: outputs are 1920x1080 and
  1080x1920, audio and video durations match (18.77 s vs 18.76 s), loudness −13.9 LUFS (target −14),
  captions placed correctly, the clip beat loops to cover its line. ~1 s of render per second of video.
- Not yet tested with real Higgsfield output: the account has 10 credits, less than one Short (~35).
- Design choice: default to AI stills + free local motion instead of Higgsfield's all-clip
  pipeline, which costs ~4x. `--motion` still routes to that pipeline for premium videos.
