# Executable timeline and handoff

## Mapping decisions to data

The source library is evidence and available media; it is not the timeline. Select only shots needed for THIS video. Record the creative outline with the intended feeling, opening, coherent development and ending; use a CTA only when it suits the purpose. Explain key source choices and omitted repeated takes in reason (maximum 2000 characters).

Use actual IDs and context tokens: project_id, memory_revision, base_fingerprint, selected_assets (1–12 IDs), asset_fingerprints (exact map), reason, renderer, ratio, clips. Optional export_settings sets resolution (1080 or 4k) and fps (30 or 60); omitted values preserve the open work settings, default 1080/30. Basic refuses 4K/60 and independent layers. Optional layers supplies independent overlays. Optional title names a new work. Optional work_id revises the exact already-open work. The JSON schema in plan.schema.json documents the payload; source duration and stale/work checks remain runtime validations.

renderer is remotion when available_renderers.remotion is true, otherwise hyperframes when available; basic is a fallback that refuses independent layers and has no timed text support. Honor an explicit engine choice when available. ratio is 9:16 or 16:9. Clips last at least one frame at the selected export fps for Remotion. At most 100 sequential clips. No arbitrary JSX, remote media URLs or asset imports in a plan.

Each clip has asset, start, end, text; optional motion, textY, textStart, textEnd, mute. No other clip fields. start/end are SOURCE seconds and satisfy 0 <= start < end <= source duration. text is <=90 characters; empty string means no overlay. motion is inherit/plain/kinetic/paper/fade/pop/blur. textY is 15–75 percent (24 top, 45 middle, 63 lower are convenient positions, not face-safe guarantees). textStart/end are relative to the TRIM: 0 <= textStart < textEnd <= end-start. Omit both for a full-clip overlay. mute defaults false.

## Independent layers (preferred for new agent videos)

Keep new clips.text empty and put each editable phrase, supplied photo or icon in the top-level layers array. Each layer has its own timeline lane and can overlap other overlays or span several sequential clips without cutting speech. Never burn designed text into intermediate video pixels when an editable text layer can express it. Text already recorded in source pixels cannot be edited as a text field.

At most 100 layers. Required id is a unique 8–32 lowercase hexadecimal string; type is text/image/icon; end must exceed start. start/end are GLOBAL seconds from the video's beginning, not source or clip-relative seconds. Default start is 0; runtime bounds are 0–86400. Keep requested visible intervals inside the actual video duration. name is at most 100 characters. Common fields: x/y center anchor (0–100 percent), width (1–100 percent of frame), opacity (0–1), rotation (-180–180 degrees), motion (plain/kinetic/paper/fade/pop/blur), enabled (boolean). Array order sets visual stacking above footage and legacy captions; later items are in front. Optional enterDuration/exitDuration are 0–5 seconds (0 means instant); exitMotion is none/plain/kinetic/paper/fade/pop/blur. Motions are clamped to half the visible interval to preserve a reading hold. No separate zIndex/track keys.

Text layers accept text (<=500 characters; use short readable phrases), font (locally available Hacen Beirut or Alexandria), fontSize (16–240 at 1080 frame width), color (six-digit hex). Defaults: x/y 50, width 70 for text/30 for media, opacity 1, rotation 0, motion plain, enabled true; font follows saved typography, fontSize 64, color white. Explicitly choose project-approved font/color/placement. The layer font/color are independent of legacy clip captions; changing copy doesn't change recorded speech. Each word can be its own editable timed text layer. Sentence-wide karaoke highlighting, animated underlines and face tracking are not connected.

Images/icons use asset from context.overlay_assets, never a source video ID, path, URL, JSX or embedded base64 in a plan. Import a requested local asset first: python3 workflow.py import-image --project ID --file /absolute/photo.png --kind image (or icon). PNG/JPEG/WebP <=8 MB, <=24 megapixels are locally sanitized to static PNG (transparency preserved, dimensions capped at 4096); SVG is refused and animation is not retained. An icon is a supplied/imported image asset, not an automatic icon generator. Retrieve fresh context after import, then use the returned registry ID. Preserve dependency/asset licenses; do not redistribute private assets.

NEW work: omitted layers defaults to []; explicit layers are saved only to this work. EXISTING revision: retrieve that exact open work's layers; include the full updated array to change it. Omitted layers preserves existing layers for compatibility; [] explicitly clears them. Preserve unrelated manual layers/IDs/stacking when revising one element. Runtime validates IDs, fonts, imported assets and finite numeric values; image hashes are checked again before actual export. Work, memory and source conflict guards still apply.

Example overlay objects (replace image asset with an imported project ID):

```json
[
  {"id":"aabbccdd","type":"text","name":"العنوان","text":"تعلّم خطوة بخطوة","start":0.2,"end":3,"x":50,"y":63,"width":75,"font":"Hacen Beirut","fontSize":76,"color":"#ffffff","motion":"fade"},
  {"id":"bbccddee","type":"icon","name":"أيقونة","asset":"IMPORTED_ASSET_ID","start":1,"end":3,"x":80,"y":35,"width":15}
]
```

Do not put layer fields in clip objects. Video overlap, arbitrary transitions/zoom/face tracking/background effects remain unsupported clip keys. Imported voice audio and legacy work typography use the verified save/editor controls, not invented plan keys.

## Word captions and direct video editing

Manual editing needs no creative agent. Import a local source file with workflow.py import-video --project ID --file /absolute/video.mp4, or the editor's ＋ فيديو; originals stay read-only and the source is retained by rescans. The UI adds its full duration to the current timeline; start a separate work first when that is intended.

Select a timeline clip. workflow.py transcribe --project ID --clip CLIP_ID starts full local speech transcription without visual model analysis or project identity generation. Poll status before continuing. Reuse an unchanged cached transcript. workflow.py caption-suggest --project ID --clip CLIP_ID --mode words|segments returns proposed layers only; retrieve fresh context and explicitly include them in a plan/save to apply. Source word/segment times are intersected with the actual trim and mapped to the clip's global offset. Changed source/work/edit state is refused. Automatic words/timing still require review; missing words cannot be invented. Existing manual captions are preserved and the 100-layer limit refuses overflow instead of truncating silently.

The Captions panel lists copy and global start/end for each word/phrase, permits search, selection and individual deletion. Splitting a layer at the playhead creates two editable intervals; delete or change only the intended fragment. Converting an existing phrase to word layers estimates durations by word length, labels timing as approximate and does not claim speech alignment. The local transcript path is the option for source-aligned automatic word times. Words appear as separate overlays, not a sentence karaoke highlight effect.

## Existing clip captions

Legacy clips retain one editable <=90-character caption per clip. Their textStart/textEnd are relative to that clip's trim, unlike global layers. Preserve them for existing work revisions unless the user asks to convert. Phrase-level timing is supported; per-word highlighting is not. Independent text layers avoid splitting continuous speech merely to change displayed copy.

## Timeline UI

The preview is immediately above the timeline. VIDEO contains sequential source trims. Every independent text/image/icon has its own lane. The legacy TEXT row appears only when clip captions exist; a silent/empty-caption video still has its VIDEO bar. AUDIO/VOICE show saved audio context. Video tracks remain sequential.

The user can add text/image/icon using the three plus buttons, select its bar to edit spelling/font/color/size/timing/position/motion, drag it in the preview to place it, drag its bar for timing or its end handle for duration, duplicate/hide/reorder/delete it, save and export. Scrubbing updates visible layers immediately. Layer entrance/exit preset and duration, image/icon replacement, word splitting and deletion are available in its inspector. Clip trims, splitting (S; applies to selected overlay when one is selected), reordering and zoom remain available. Global overlay times stay explicit after clip reorder/trim: inspect and adjust their intervals to the new sequence. Save/undo/history belong to the selected independent work. Return the exact project+work editor URL.

## Cutout

For requested selfie background blur/color, read available_renderers.cutout and use cutout --project ID --work WORK_ID --clip CLIP_ID --base-fingerprint TOKEN --mode blur|color --color '#172a25'. This transforms only the selected trim into a derived MP4, preserving source range and audio provenance; stale work/source/edit tokens refuse replacement. Poll status then fresh context. Original/history remain; rescans retain derived assets. Processing: <=120 seconds, 30fps, SDR, 720p with long side <=1280. It supports people, blur/solid background, not transparent layers or arbitrary replacement media. Review hair and motion edges. 1080 export cannot restore source detail lost during 720 processing.

Manual editor shortcuts: Backspace/Delete removes the selected layer or clip from the draft; ⌘Z/Ctrl+Z undoes unsaved manual edits; ⌘⇧Z/Ctrl+Shift+Z (also Ctrl+Y) redoes; ⌘S/Ctrl+S saves; Space plays; S splits. Typing fields keep native text deletion/undo. Session edit history is scoped to the current work; saved history remains available after reloading. The original source file is never deleted.

Shift-click (also Command/Ctrl-click) selects independent layers in the timeline, caption list or preview. Move their shared centre with Group X/Y or drag a selected preview layer; Group Size scales text fonts, image/icon widths and relative spacing together within supported limits. Delete removes all selected layers and Undo restores them. Clip selections stay individual.
