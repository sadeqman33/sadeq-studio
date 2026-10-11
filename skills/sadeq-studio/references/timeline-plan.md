# Executable timeline and handoff

## Mapping decisions to data

The source library is evidence and available media; it is not the timeline. Select only shots needed for THIS video. Record the creative outline with the intended feeling, opening, coherent development and ending; use a CTA only when it suits the purpose. Explain key source choices and omitted repeated takes in reason (maximum 2000 characters).

Use actual IDs and context tokens: project_id, memory_revision, base_fingerprint, selected_assets (1–12 IDs), asset_fingerprints (exact map), reason, renderer, ratio, clips. Optional title names a new work. Optional work_id revises the exact already-open work. The JSON schema in plan.schema.json documents the payload; source duration and stale/work checks remain runtime validations.

renderer is remotion when available_renderers.remotion is true, otherwise hyperframes when available; basic is a fallback with no timed text support. Honor an explicit engine choice when available. ratio is 9:16 or 16:9. Clips last at least one 30fps frame for Remotion. At most 100 sequential clips. No arbitrary JSX, remote media URLs or asset imports in a plan.

Each clip has asset, start, end, text; optional motion, textY, textStart, textEnd, mute. No other clip fields. start/end are SOURCE seconds and satisfy 0 <= start < end <= source duration. text is <=90 characters; empty string means no overlay. motion is inherit/plain/kinetic/paper/fade/pop/blur. textY is 15–75 percent (24 top, 45 middle, 63 lower are convenient positions, not face-safe guarantees). textStart/end are relative to the TRIM: 0 <= textStart < textEnd <= end-start. Omit both for a full-clip overlay. mute defaults false.

Do not submit font, colors, word-highlighting, icons, transitions, zoom, face tracking, video overlap or background effects as invented clip keys. Font/palette/academy styling and imported voice audio are saved editor/work settings. Changing them requires the actual editor or verified save API with fresh state; the plan alone does not set them. Read context typography and choose text that works in its current rendering. If the visual brief needs an unsupported element, explain the exact gap and deliver only the authorized supported portion.

## Text rhythm without cutting speech

Only one overlay exists per clip. A requested phrase sequence can split a continuous source take into contiguous trims with distinct text, keeping every spoken word and small breathing margins. Check there is no gap/overlap in source times and no truncation of negation or a price. This produces phrase-level timing; it is not a per-word karaoke track. A long complete sentence may span several clips while its audio stays continuous.

## Timeline UI

The preview and timeline sit together. VIDEO shows sequential source trims; TEXT shows their timed overlay intervals; AUDIO/VOICE show the saved original/background/imported voice context. These are not unrestricted overlapping NLE tracks. Keep source audio unless the current request calls for a mute or replacement.

The user can click a clip to edit its text, in/out, position and text preset, change the font in supported typography controls, scrub the ruler, zoom, split at playhead (S), duplicate and reorder. Save belongs to the selected independent work. Undo stays in that work. Return the specific editor link so the user never opens a different video's timeline.

## Cutout

For requested selfie background blur/color, read available_renderers.cutout and use cutout --project ID --work WORK_ID --clip CLIP_ID --base-fingerprint TOKEN --mode blur|color --color '#172a25'. This transforms only the selected trim into a derived MP4, preserving source range and audio provenance; stale work/source/edit tokens refuse replacement. Poll status then fresh context. Original/history remain; rescans retain derived assets. Processing: <=120 seconds, 30fps, SDR, 720p with long side <=1280. It supports people, blur/solid background, not transparent layers or arbitrary replacement media. Review hair and motion edges. 1080 export cannot restore source detail lost during 720 processing.
