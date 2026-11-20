# Prompt templates

Replace `[BRACKETS]`. Keep everything else word for word.

---

## Shared style block (paste into stages 1, 2, 3)

```
RENDER STYLE: a frame captured from a PS2 era open world game, not an illustration, not a modern low poly art filter, not a photo with an effect on top. Low total polygon budget, simplified shapes, slightly blocky low detail silhouettes, but shaded with smooth interpolated per vertex lighting and soft gradient transitions between surfaces. No hard flat triangulated panels, no visible individual facets. Materials read as matte and slightly plastic, a console era finish with soft highlight falloff. No subsurface scattering, no pore or fiber detail, no photographic texture. Console era texture resolution, slightly soft and compressed, with mild seams at UV boundaries.

COLOUR GRADE: pale and slightly desaturated, flat early 2000s console output, soft clipped highlights, a faint neutral cast. No warm cinematic colour, no rich saturated tones, no moody contrast. Optional: very subtle scan lines and a soft vignette at the corners, kept light.

NEGATIVE: photorealistic skin, real camera grain, modern high poly render, ray traced lighting, ambient occlusion, cinematic shadows, flat faceted triangle mosaic, subsurface scattering, depth of field blur, distorted anatomy, extra limbs, extra fingers, text, captions, watermark, real brand names or logos.
```

---

## Stage 1 — Character reference sheet (GPT Image 2, 16:9)

This is the guide's original prompt. It has been checked and is kept as written, with small cleanups.

```
Generate a single wide landscape image, 16:9, composed as a three panel character reference sheet divided into three equal vertical panels of identical width, separated by thin dark vertical gutters. All three panels share one continuous flat dark grey background, like a game character select screen, with no props, no text, no logos, no watermarks, no captions, no labels.

CHARACTER: [age, build, skin tone, face shape, hairstyle and hair colour, defining features]
OUTFIT: [each garment with colour, plus shoes and accessories]

The same character, with identical face, hairstyle, build and outfit, appears in all three panels. Invent a plausible back view of the clothing and hair consistent with the front. Keep proportions natural and realistic, not exaggerated or glamour styled.

PANEL 1, left: full body front view, face visible. The character stands facing camera straight on, centred, feet flat and about hip width apart, arms relaxed at the sides, weight even, neutral expression, eyes to camera. Full figure head to feet in frame with a little space above and below. A soft contact shadow under the feet.

PANEL 2, centre: full body back view. The identical character turned 180 degrees away from camera, same scale, stance and floor baseline as Panel 1. Back of the head and hair visible. No face and no profile edge shows. Same contact shadow.

PANEL 3, right: close up portrait. Head and shoulders only, face turned very slightly off axis, eyes to camera, neutral expression, collar or neckline visible at the bottom. Simplified generic facial features, still recognisable as the same character.

[SHARED STYLE BLOCK — but write "a character model captured from" instead of "a frame captured from"]

LIGHTING (identical in all panels): a single soft key light slightly above eye level with gentle falloff. No dramatic directional shadow, no rim light, no coloured spill, no bounce light, no global illumination.

CAMERA (identical in all panels): eye level, static, no tilt, no wide angle distortion, no depth of field, everything in hard uniform focus.

CONSISTENCY: three panels only, equal width, in this order: front full body, back full body, close up portrait. Identical body scale between Panels 1 and 2. Identical outfit, render style, lighting, grade and background value in all three panels.

Additional NEGATIVE: different outfits between panels, changed hairstyle between panels, face visible in the back view, side profile in the back view, exaggerated proportions, glamour styling, heavy makeup, environmental background, additional panels, tilted camera.
```

---

## Stage 2 — Location / establishing frame (GPT Image 2, final ratio)

```
Generate a single [16:9 | 9:16] image: an in-game establishing shot from an early 2000s open world console game.

LOCATION: [setting, e.g. "a sun-bleached coastal city boulevard at late afternoon"]
DETAILS: [key elements: buildings, vehicles, props, signage shapes (no legible words), weather, time of day]
CAMERA: [game-camera framing, e.g. "third-person chase camera height, slightly above eye level, looking down the street"; or "high cutscene crane shot over rooftops"]
ATMOSPHERE: short draw distance with soft distance fog, sparse low-detail background buildings, repeating tiled textures on roads and walls, simple sprite-like trees, blob shadows under objects.

The scene is empty of people and characters: it is a backplate for adding characters later. Leave clear space at [left | centre | right] for a character.

[SHARED STYLE BLOCK]

LIGHTING: one dominant sun or key light with simple soft shadows; baked, flat-looking ambient; no global illumination, no volumetric god rays, no lens flare.
```

---

## Stage 3 — Keyframe composite (Nano Banana 2.1, final ratio)

Connect: the location image + 1–2 character sheets. Name each reference in the prompt.

```
Using image 1 as the environment and the character reference sheet(s) as the exact character design, create a single [16:9 | 9:16] in-game frame.

Place [CHARACTER NAME] (from the reference sheet, identical face, hair, build and outfit) [position in frame], [action / pose, e.g. "mid-stride walking toward camera, hands in jacket pockets"], [expression].
[Optional second character: name, position, action, relation to first.]

Keep the environment from image 1 unchanged in layout, camera angle, lighting and colour. Match the character's scale to the environment and add a soft blob contact shadow under their feet. The character must share the scene's low-poly console render style, not look pasted in.

SHOT: [beat name, e.g. "character reveal", "rooftop standoff"]. CAMERA: [game camera or cutscene framing].

[SHARED STYLE BLOCK]

Additional NEGATIVE: changed outfit, changed face, photoreal character on low-poly background, mismatched lighting, cutout halo edges, duplicate characters.
```

---

## Stage 4 — Trailer video (Seedance 2.5)

Connect all stage-3 keyframes as Image References, in shot order. Make the beat timings add up to the clip length.

```
A [30]-second trailer for an original early 2000s open world console game called "[FICTIONAL TITLE]", rendered exactly like real PS2-era in-game footage and cutscenes: low-poly models, per-vertex lighting, soft compressed textures, short draw distance with fog, pale desaturated colour, stiff slightly robotic character animation, simple physics.

Use the reference images as the keyframes, in order:
0–[x]s: [shot 1 — e.g. "slow crane over the city skyline at dusk"]
[x]–[y]s: [shot 2 — e.g. "lead character walks out of a diner toward camera, chase camera follows"]
[y]–[z]s: [shot 3 — action beat]
[z]–[w]s: [shot 4 — kingpin reveal, cutscene framing]
[w]–30s: hard cut to black, then title card "[FICTIONAL TITLE]" in chunky 2000s game-logo type, subtle scan lines.

Camera moves like a game camera: smooth third-person follow, simple cutscene pans, abrupt hard cuts between shots. Keep every character identical to the references. No photorealism, no cinematic depth of field, no modern lighting, no real brands or logos.
```

If the video morphs between shots, render one clip per beat (each with only its keyframe) and join them in the Composition node.

---

## Stage 5 — Soundtrack (Music Gen, lyrics off for instrumental)

```
[30]-second instrumental for an early 2000s open world video game trailer. [Genre, e.g. "West Coast G-funk" | "pop-punk" | "trip-hop" | "big-beat electronica" | "orchestral-lite with breakbeats"], [tempo] BPM. Slightly compressed, lo-fi console-era mix like a PS2 game soundtrack or in-game radio station. Starts with a short atmospheric intro, the beat drops at [x]s for the action, builds through the reveals, and ends on a hard stop or stinger at [w]s for the title card. No vocals.
```

Mix note: in Composition, set the music under any game SFX. Make sure the stinger lands exactly on the title-card cut.
