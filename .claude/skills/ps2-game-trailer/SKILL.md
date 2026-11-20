---
name: ps2-game-trailer
description: Plan and write every prompt for a 2000s / PS2-era low-poly "video game trailer" made with AI (character sheets, locations, composited keyframes, video, music). Use when the user wants a nostalgic console-era game trailer, a "GTA-style" / PS2-style AI video, low-poly character reference sheets, or an ElevenCreative Flows / Seedance / Nano Banana pipeline for retro-game footage.
---

# PS2-Era AI Game Trailer

Builds a ~30 s trailer that looks like footage from an early-2000s open-world console game.
Five stages; each one feeds the next as image references. You (Claude) write all prompts —
the user only pastes them into their tool.

Source: ElevenCreative's "Make a 2000s video game trailer with AI (full guide)" (X, Nov 2026).
Model availability verified on elevenlabs.io in Nov 2026 — re-check if much time has passed.

## 0. Brief first (ask, don't assume)

Ask in one message, offering defaults:
1. **Premise / genre** — crime saga, skate, racing, sci-fi, fantasy? One-line hook.
2. **Crew** — default 3: lead, kingpin/rival, sidekick. A few words of look per character.
3. **City / settings** — 3–5 key locations (street, rooftop, interior, vehicle, landmark).
4. **Beats** — 4–6 shots (intro, character reveal, action, chase, title card).
5. **Format** — 16:9 (YouTube/X) or 9:16 (Reels/TikTok). Default 16:9, 1080p.
6. **Tool** — ElevenCreative Flows (default), or another stack (Higgsfield MCP, etc).

If the user says "just go", invent an original premise and proceed.

## Pipeline

| # | Stage | Node / model (ElevenCreative) | Inputs | Output |
|---|---|---|---|---|
| 1 | Crew sheets | Image Gen · **GPT Image 2** (2.6 also listed) | prompt | 1 three-panel sheet per character, 16:9 |
| 2 | Locations | Image Gen · GPT Image 2 | prompt | 1 empty establishing frame per setting, final ratio |
| 3 | Keyframes | Image Gen · **Nano Banana 2.1** | location + character sheet(s) + prompt | 1 frame per shot, character posed in scene |
| 4 | Video | Video Gen · **Seedance 2.5** (native up to ~30 s) | all stage-3 frames as Image References + prompt | trailer clip |
| 5 | Soundtrack | Music Gen (lyrics **off** for instrumental) → Composition node | prompt; then video + music | final MP4 |

Write all prompts from `references/prompts.md`. Rules:
- Paste the **shared style block** from that file into stages 1–3 unchanged. One style, word for word, is what keeps the frames consistent.
- **Ratio lock:** stages 2, 3 and 4 all use the final video ratio. Stage 1 sheets are always 16:9.
- One character sheet per character. Make it again if the face or outfit drifts. Don't patch it in later stages.
- Write fictional names only. No real brands, logos, team names, real people or existing game IP (the *style* is fine, but no "GTA" logos, characters or map recreations). Put a made-up game title on the title card.

## Deliverable

Give the user a **production sheet**:
1. Brief recap (premise, crew, settings, shot list with seconds per beat, adding up to the video length).
2. Numbered, copy-ready prompts in code blocks, grouped by stage, each labelled with model, ratio, and which nodes to connect into it.
3. Stage 5 music prompt + mix note.
4. A QA checklist (below).

If image/video generation tools are connected (for example `mcp__higgsfield__generate_image` / `generate_video`), offer to run the stages directly. Show the cost estimate first and get a yes before spending credits.

## QA checklist (run before calling it done)

- [ ] Same face/hair/outfit across the sheet panels and in every keyframe
- [ ] No photoreal skin, depth-of-field blur, ray-traced shine, or faceted "low-poly filter" look
- [ ] Pale, slightly desaturated grade everywhere (no teal-orange cinema look)
- [ ] All keyframes and the video share one aspect ratio
- [ ] No legible real-world text or logos; title card uses the fictional name
- [ ] Shot durations add up to the video length; music length matches

## Troubleshooting

| Symptom | Fix |
|---|---|
| Looks like a modern render / too glossy | Re-add NEGATIVE line; stress "PS2 era, per-vertex lighting, compressed textures" |
| Faceted triangle mosaic | Emphasise "smooth interpolated shading, no visible facets" |
| Character drifts in keyframes | Connect the sheet again; name the character + outfit explicitly in stage-3 prompt |
| Back view shows a face | Add "no face, no profile edge" again; regenerate the sheet |
| Video morphs between shots | Fewer refs per run; generate per-beat clips, then join them in Composition |
| Music too cinematic | Add "lo-fi console soundtrack, compressed, 2000s game menu" |
