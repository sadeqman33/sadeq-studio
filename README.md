# Sadeq Studio

**By Sadeq Ammar · صادق ستوديو**

A local video workflow for Codex: describe the project, style and feeling in a chat; the agent uses saved project knowledge to create an editable video. Open that video's own timeline, make small changes by hand, then export MP4.

## هوية الواجهة · 0.19.1

واجهة فحمية مع إجراءات بنفسجية، ألوان مستقلة لأنواع الطبقات، إعدادات تصدير مجمعة ووضع تركيز يوسّع المعاينة والتايم لاين. تغيير الواجهة لا يغيّر ألوان هوية المشاريع أو محتوى المسودات. دليل الاختصارات متاح من شريط الأقسام.

## إنشاء مباشر داخل Studio · 0.19.0

زر **فيديو بالإيجنت** يفتح ثلاث خطوات: الفكرة والمقاطع، الشكل والحركة، ثم إعدادات الملف والمراجعة. زر الإنشاء الأخير يشغّل Codex مباشرة، وبعده يفتح فيديو مستقل قابل للتعديل. تختار MP4 مع مسودة أو مسودة أولاً. تبقى طريقة الطلب من محادثة Codex متاحة.

الخيارات تشمل نوع الفيديو، إيقاع ومدة مستهدفة، كلمة أو كلمتين من التفريغ الآلي بدون تنقيط، خط، ميزات وأيقونات المشروع المطابقة، أربع طرق ظهور، موضع، صوت أصلي أو كتم، مقاس عمودي أو أفقي، 1080p/4K و30/60 fps. المدة والإيقاع توجيه للإيجنت؛ الحركات والتوقيت والكابشن والدقة تنطبق على الطبقات فعلياً. الكابشن يُحجب خلال ظهور الميزة. لا يولّد لقطات أو أيقونات أو صوتاً جديداً.

الإعدادات في المتصفح محفوظة لكل مشروع، وإعدادات الفيديو النهائي محفوظة داخل عمله المستقل. أول تشغيل يحلل المختار والمراجع المعتمدة المحتاجة فقط. يستعمل مسار Codex الموجود (النص والصور المنتقاة حسب إعداداته)، والتفريغ والتصدير محليان. الحركات الأوسع والكاميرا تبقى بمكتبة المراجع ولا يوهم الزر بتطبيق محركات غير موجودة.

API: `POST /api/create-video` takes `id`, `work_id`, `base_fingerprint`, `assets` (1–12 unique IDs), `request`, and validated `settings`. It rejects stale/busy/cross-project requests, checks source fingerprints before committing, creates an independent work only after validating the whole plan, and exposes `analysis/planning/layers/render/done` job stages. Render failures retain the editable new work. Existing projects/works are not migrated by this UI update.

## شلون يشتغل؟

1. تربط ملف معلومات أو مجلد المشروع من الواجهة.
2. تحليل المشروع يحفظ المعرفة والهوية؛ لكل فيديو تحليل منفصل وتفريغ كلام آلي يحتاج مراجعة.
3. تطلب الفيديو من محادثة Codex باستخدام `sadeq-studio`، مع المشروع والستايل والإحساس المطلوب.
4. كل فيديو ينحفظ كمسودة وتايم لاين مستقل. تختاره من **فيديوات المشروع → فتح التايم لاين**.
5. تعدّل النص والخط والتوقيت والقص والترتيب والصوت، تحفظ وتصدّر.

معرفة المشروع ومكتبة المصادر مشتركة؛ المونتاج والتراجع والتصديرات مستقلة لكل فيديو.

## Features

- Persistent project identity in PROJECT.md, STYLE.md and LEARNINGS.md, backed by typed JSON.
- Per-video drafts, timelines, history and versioned exports.
- Arabic text, local fonts, clip trims/order/mute, timed text and six text motion presets (plain, slide, paper, fade, pop, focus).
- Local Remotion and Hyperframes 1080p rendering, plus a basic 720p renderer.
- Optional local full-audio speech transcription on Apple Silicon.
- Imported voice-over or music with trim, offset, gain and source-audio controls.
- Iraqi creative review and manually recorded outcomes; editorial scores are not calibrated virality probabilities.
- Conflict guards for project identity, source files and the active video work.

## Requirements

Currently tested on **macOS**. Manual editing can run without an agent account; agent analysis needs the Codex CLI and your own authenticated account.

- Python 3.10+.
- Node.js 22.12+ and npm.
- FFmpeg / FFprobe on PATH.
- Codex CLI on PATH for agent tasks.
- Locally installed Arabic fonts: Hacen Beirut and, optionally, Alexandria. Font files are not redistributed. You can point the configuration to fonts you are permitted to use.

## Install and run

```sh
git clone https://github.com/sadeqman33/sadeq-studio.git
cd sadeq-studio
python3 -m pip install -r requirements.txt
npm ci
npx playwright install chromium
```

For the 1080p renderer on macOS, run `./setup-hyperframes.command` once. It installs the pinned npm dependencies and the renderer's managed browser.

```sh
python3 server.py --port 8794
```

Open **http://127.0.0.1:8794**. The server binds to loopback only. On macOS, `start.command` opens the browser and keeps the server running while its terminal is open.

A fresh checkout starts with **no projects**. Add your own folders through the UI. All project data and render output stay in the local data directory; original source files are not overwritten.

## Configuration

Set environment variables before starting the server:

| Variable | Purpose |
| --- | --- |
| SADEQ_DATA_DIR | Project data location; defaults to `./data` beside server.py. |
| SADEQ_MEDIA_ROOT | Additional root for resolving a project folder name. Full paths are preferred. |
| SADEQ_FONT_DIR | Local font folder; defaults to `~/Library/Fonts`. |
| SADEQ_FONT_HACEN | Font path used for the Hacen Beirut choice. |
| SADEQ_FONT_ALEXANDRIA | Font path used for the Alexandria choice. |
| SADEQ_NODE | Node executable for rendering. |
| SADEQ_CHROME | Optional installed Chrome executable for basic text rendering and Remotion. |
| SADEQ_PLAYWRIGHT | Optional installed Playwright module path; defaults to the npm dependency. |
| SADEQ_ASR_PYTHON | Optional transcription environment's Python executable. |
| SADEQ_ASR_MODEL | Local Whisper model snapshot folder. |

For example, if your fonts have different filenames, point the two font variables to their actual local paths. Fonts must exist before using the corresponding typography choice.

## Remotion renderer (0.11)

Choose **Remotion · 1080** in the editor's render engine selector, save, then export. The calling agent may submit `renderer: "remotion"` in the same guarded plan schema. Timed text and typography edits retain your selected 1080p engine.

Run `./setup-remotion.command` once to install pinned packages. Remotion 4.0.534, @remotion/bundler and @remotion/renderer use matching versions. Existing local Chrome is used when available; otherwise Remotion obtains its managed browser on first render.

Our fixed React composition converts your independent timeline into local footage sequences and Arabic overlays. It shares the editor's deterministic text motion. Source trims/audio and mute stay in the local FFmpeg pipeline; imported voice/music are mixed afterwards. Editable JSON, React input props and render logs remain with each local export. Timings round cumulative boundaries to the selected 30/60 fps (at most half a frame at a boundary); clips shorter than one frame are rejected. No arbitrary agent-written JSX, cloud rendering or generated footage is connected.

Remotion has its **own license**, not an MIT license. Read [the upstream terms](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) before commercial use. A company license may be required depending on the organization. We preserve the license notice and do not sell or relicense Remotion itself. No license purchase or account connection is automated.

## Speech take selection (0.12)

The agent now receives source-timed speech candidates and possible repeated takes from each selected video's saved transcript. It compares whole phrases for the requested idea, prefers coherent attempts, and preserves meaning, negation, names, numbers and qualifiers. Suggested cuts use real source timecodes and remain editable. No source audio or existing timeline is deleted automatically.

Open a library video's **≡ → اختيار محاولات الكلام** to compare candidates and seek to their original audio. From a chat, use `python3 workflow.py speech-picks --project ID --asset ID`; selected `context` evidence includes the same suggestions. Current cached transcripts work immediately without re-analysis. New transcription also saves recognizer metrics.

The local detector flags possible textual repetition, correction/restart cues and unfinished endings. These are **ASR editing hypotheses**, not a guarantee of detecting stutters, determining a factual error, or measuring vocal performance. Word boundaries are used only when they match the transcript; otherwise it keeps segment ranges. Ambiguous factual differences require context/listening review. The calling agent makes the final editable plan; no second planning agent or private audio upload is added.

## Optional transcription

On Apple Silicon, run `./setup-transcription.command`. It creates `.venv-asr`, installs the speech dependencies and downloads Whisper weights once. Subsequent transcription runs use local audio and cached model weights. Visual analysis sends selected frames and automatic transcript text to the user's Codex model; transcription alone does not upload audio to a video service.

## Agent workflow

The plugin is **Sadeq Studio**, authored by **Sadeq Ammar**, with workflow tag `$sadeq-studio`. The repository includes synchronized portable/Codex manifests and `skills/sadeq-studio/SKILL.md`. Build the distributable source package with `python3 build_package.py`, then install through Codex Plugins.

Before using an installed plugin with existing projects, save `~/.config/sadeq-studio/runtime.json` locally with `{"runtime_root": "/absolute/path/to/your/existing/studio"}`. Choose the app directory already holding your project data, not the installed plugin cache. Verify it contains workflow.py and server.py. The skill reads this configuration before using the existing local service; it never moves your projects or starts an empty duplicate registry. Runtime paths and private brand references remain outside the published package. After installing, open a new chat and select Sadeq Studio or invoke `$sadeq-studio`.

The plugin contains 16 discoverable skills. The main skill routes a request through only the required stages, sharing one execution contract and the actual structured timeline schema.

| Stage or production mode | Packaged skill |
|---|---|
| Main workflow | sadeq-studio |
| Identity, purpose and lasting approved style | project-memory |
| Source content, stills, visible text and full-audio ASR | video-analysis |
| Complete spoken takes and repetition hypotheses | speech-edit |
| Accurate Arabic copy, typography and shot-specific placement | arabic-product-video |
| Talking/product reels, montage, text motion, episode clips | video-ad-editor, montage-video, motion-video, podcast-video |
| Requested separate cover image and explicit external-editor handoff | thumbnail-video, davinci-video |
| Distinct ad concepts and Iraqi evidence-based review | meta-ads-diversity, iraqi-video-review |
| Independent timeline, manual voice-over and actual export | timeline-edit, voiceover, export-video |

Shared references cover what to extract from footage, style precedence, the six text presets, global independent layers, legacy relative caption timing, source/identity/work conflict tokens, manual finishing and observable export review. Saved brand memory/private approved style notes remain local and are read at execution time. User-authored Arabic/Meta/Iraqi preferences are incorporated into the package; production modes have original Studio-specific instructions, without copying the external plugin's separate engine/scripts.

The standard supported path is real source footage → saved identity/evidence → coherent source trims → editable timed text/image/icon layers → independent editable work → MP4. Mode skills explicitly identify limits: generated 3D/collage scenes, sentence-wide karaoke highlighting, multicamera/face tracking, a native DaVinci bridge and an automatic Lahajati API are not connected. Imported cover art can be a timed image layer; automatic cover generation/full-frame insertion is not connected. Including an instruction skill does not create those renderer features.

The **calling chat** is the creative agent. Useful CLI commands:

```sh
python3 workflow.py projects
python3 workflow.py context --project PROJECT_ID
python3 workflow.py works --project PROJECT_ID
python3 workflow.py open-work --project PROJECT_ID --work WORK_ID
python3 workflow.py submit --plan-file /absolute/path/plan.json --render
python3 workflow.py status --project PROJECT_ID
```

A new agent plan creates a new work. To revise an existing video, open its work first, read fresh context and submit its exact work_id. The skill describes the plan schema and conflict checks.

## Voice-over

Lahajati is currently a manual workflow: prepare copy, generate and download audio at https://lahajati.ai/en, then import it into the editor. Automatic Lahajati generation/API integration is not connected. Editing the written script does not alter an imported recording.

## Current limits

- Sequential video clips with independent text/image/icon overlay lanes; video/audio overlap is not a full multitrack nonlinear editor.
- Visual analysis samples stills; it does not watch every frame or verify motion/audio performance.
- Speech text is automatic and needs human review.
- No generated scenes/images, automatic publishing, live trend feed, account metrics integration or virality prediction model.
- HDR input requires conversion before export. 1080p rendering may take time.
- No fonts, models, source footage, saved project memories or previous exports are included in this repository.

## Validate and package

```sh
python3 -m unittest discover -p 'test_*.py'
node --check app.js
python3 build_package.py
```

The render tests need FFmpeg, fonts and installed browser/runtime dependencies. Tests use temporary generated media and their own data directory. The package builder includes only reviewed source files and produces an ignored ZIP under dist/.

## Ownership

Copyright © 2026 **Sadeq Ammar**. Original application/workflow rights are reserved; see COPYRIGHT. Public source availability does not grant an open-source license. Dependencies retain their own licenses in third-party/ and their installed distributions.

## Editing surface and local selfie backgrounds (0.13)

The timeline sits directly below the preview. Click its ruler to seek, zoom for small cuts, use S to split at the playhead, duplicate/reorder clips and apply six text presets or top/middle/lower positions. Changes preview immediately and stay in the current independent work. Split preserves the total source range and clips text timing into each resulting segment. Each resulting clip has its own animation envelope. The save indicator shows unsaved changes; save before switching/exporting. Extra project works and audio/review panels stay below the editor.

Run `./setup-cutout.command` once (Python 3.10+ and a compatible MediaPipe wheel). It installs pinned optional packages in .venv-cutout and downloads the official SelfieSegmenter float16 version 1 model from Google, verified with SHA-256. No footage is uploaded. Select a selfie clip → تعديل المقطع → عزل الشخص → blur or a solid background color → process. The operation creates a derived MP4, preserves the selected original audio/range and replaces just that clip in its open work. Undo recovers the original edit. Derived sources stay in the shared library during rescans and remain private.

Current cutout scope: person segmentation, SDR, 30 fps, up to 120 seconds per selected trim, ≤720p/1280-long-edge processing, blur or solid color. Hair, motion blur and occlusion need visual review. No transparent layer, photo/video replacement background or general object matting is connected. The 1080p render can use the result but cannot recover processing resolution. Failed processing or a stale work/source leaves the timeline unchanged.

The calling chat can use `workflow.py cutout --project ID --work WORK_ID --clip CLIP_ID --base-fingerprint TOKEN --mode color --color '#172a25'` with fresh context tokens; query status, then refresh context. Optional environment overrides: SADEQ_CUTOUT_PYTHON and SADEQ_CUTOUT_MODEL. Never infer API readiness from a website login.

To verify real inference locally, supply an explicitly chosen test portrait:
`SADEQ_CUTOUT_TEST_IMAGE=/absolute/test-portrait.jpg python3 -m unittest test_cutout -v`

This package can be set up on another compatible local machine; its Codex skill needs that machine's service, files, models and fonts. It does not connect every chat platform or video editor automatically.

## Independent overlay layers (0.15)

Each video work owns a separate `layers` array. Text, image and icon layers have global timeline start/end, independent X/Y, width, opacity, rotation, enabled state and motion; array order is visual stacking order above footage/legacy captions. Text supports per-layer Hacen Beirut/Alexandria font, color and size. Imported PNG/JPEG/WebP images/icons (up to 8 MB, <=24 megapixels) are converted locally to sanitized PNG, preserving transparency, and shared within that project. SVG/animated image layers are not supported. Originals remain read-only.

Use ＋ نص / ＋ صورة / ＋ أيقونة on the timeline. Every layer has its own lane. Click it to edit; drag inside the preview for placement, drag its bar for timing, and drag its end handle for duration. You can duplicate, hide, reorder or delete an overlay and save/undo within that independent work. Existing clip captions stay editable; empty video captions no longer appear as fake text blocks. Layers are preserved in saved works/history and frozen into actual Remotion/Hyperframes exports. Basic export refuses layers rather than omit them.

Agent plans accept optional `layers` with imported project overlay asset IDs. `workflow.py context` returns layers and `overlay_assets`; `workflow.py import-image --project ID --file /absolute/image.png --kind image|icon` imports a local asset through the existing work/conflict guards, then the agent retrieves fresh context and submits structured layers. No generated JSX or remote image URL enters the renderer. Render snapshots verify image hashes, retain private font/media locally, and use the same deterministic layer style/motion in preview and both engines. A layer changes its own copy without altering recorded narration. Video tracks remain sequential; this adds overlay layers, not overlapping video/audio NLE clips.


## Direct editing, word captions and UHD export (0.16)

Use ＋ فيديو to link a single local video and add its full duration to the current work; no creative agent is needed for manual editing. Sources stay read-only and file links survive rescans. Captions lists every text layer's global copy/time, with search and individual deletion. Select an overlay and split at the playhead (S), then change/delete only the intended fragment. Legacy clip text can be detached into its own layer or deleted without deleting footage. Each image/icon can be replaced while retaining its timing/geometry. Six entrance presets, entrance/exit duration (0–5 s) and an independent exit mode work identically in preview and both engines.

For speech captions select a clip, run local transcription (no visual/creative model call), then add words or segments from the current cached transcript. Source times map through the trim to global work times. Automatic transcription still needs word/claim/timing review. Phrase-to-word splitting is explicitly approximate; it is not ASR alignment. At most 100 overlays; overflow is refused without truncation. Words are separate overlays, not sentence karaoke highlighting. The layer preview now advances global time per animation frame while playing instead of waiting for the browser's sparse timeupdate events.

Per-work export_settings selects 1080p or 4K UHD, and 30/60 fps. Portrait UHD is 2160×3840; landscape is 3840×2160. Remotion and Hyperframes use the chosen canvas/fps throughout preparation/rendering; server verifies final encoded dimensions/cadence. Basic remains 720p/30. Low-resolution/30fps source footage is scaled/repeated as necessary, not AI enhanced/interpolated; overlays render at the chosen cadence. UHD/60 takes more render time/storage. No original footage, private project memory or fonts are packaged.

Manual editor shortcuts: Backspace/Delete removes the selected layer or clip from the draft; ⌘Z/Ctrl+Z undoes unsaved manual edits; ⌘⇧Z/Ctrl+Shift+Z (also Ctrl+Y) redoes; ⌘S/Ctrl+S saves; Space plays; S splits. Typing fields keep native text deletion/undo. Session edit history is scoped to the current work; saved history remains available after reloading. The original source file is never deleted.

Shift-click (also Command/Ctrl-click) selects independent layers in the timeline, caption list or preview. Move their shared centre with Group X/Y or drag a selected preview layer; Group Size scales text fonts, image/icon widths and relative spacing together within supported limits. Delete removes all selected layers and Undo restores them. Clip selections stay individual.

### Export performance (0.16.2)

Remotion renders with bounded CPU/RAM-based concurrency, uses WebCodecs-based @remotion/media Video with built-in OffthreadVideo fallback, mounts only active layers, caches Webpack compilation and uses tested Apple VideoToolbox H.264 on compatible Macs (high-rate 12/20 Mbps for 1080p 30/60 and 50/80 Mbps for 4K 30/60), falling back to software CRF 18 / fast encoding. Both engines retain native-or-smaller intermediate footage instead of upscaling twice, and reuse privately cached prepared ranges when only text/layers change. Final output remains at the selected full 1080p/4K and 30/60fps.

The editor displays live Remotion progress, actual frame counts and phase names; each local export includes `performance.json` timing/cache diagnostics. Preparation/audio/final verification are separate phases and may have no percentage. The disposable clip cache is capped at 8 GiB per engine/project; prior exports and original source media are preserved. Set `SADEQ_RENDER_CONCURRENCY=1..8` locally to benchmark your machine when needed.

The one-shot Remotion runner exits after the encoded MP4 has finalized and cleanup has run, avoiding idle bundler/network timers delaying handoff. `runner-timing.json` distinguishes renderer completion from process lifetime.

### Timeline usability (0.17.0)

The playhead is a keyboard-accessible slider with a drag target along its full height. Pointer updates are coalesced on animation frames; zoom remains anchored to time/pointer position. Continuous zoom, Fit All/Selection, frame stepping, optional follow-playhead and adjustable track height preserve a per-work local view. +/− zoom, F fits all, N toggles snapping, arrows step one frame (Shift=10), Home/End seek bounds; text fields retain native editing.

Caption/title/image/icon display groups pack non-overlapping independent objects and can expand to individual rows. Their saved timing and render stacking stay independent. Shift-click or Shift-drag empty space selects groups; a timeline drag moves their times together. Both edges can trim one selected layer, with frame precision and optional snapping. Double-click text for inline edits, use the compact toolbar, or resize uniformly with preview corner handles. Saved manual locks prevent accidental editor changes.

The editor requests visible source ranges only for private cached thumbnails and normalized source amplitude envelopes, with two-worker limits. Derivative previews are stored under local project `timeline-previews/`; they contain no uploaded media and never enter source packages. Source audio envelopes do not reflect final voiceover ducking/gain, and are not transcripts. Preview ranges over one hour are rejected; clips/source media are preserved.

## Motion bank (0.18.0)

The timeline's **بنك الحركات** opens 50 locally stored, numbered reference previews from Majed Video 4.5 (MIT; pinned provenance in motion-bank/SOURCE.json and third-party/majed-motion-bank). Search, filter, prefer/exclude and create per-video motion plans. Preferences and the last 100 plans persist under data/motion-bank/state.json. Plans never edit a timeline.

Sixteen native Studio adaptations are applicable to selected unlocked text layers; six also support images/icons. Use **جرّب حركة Studio** for the actual implementation preview and **طبّق على المحدد** to apply. Existing positions, sizes, fonts and text are retained; the operation uses normal draft/undo/save. Preview and both advanced export engines share bank_motion.js. Reference demonstrations are separate from native output. Camera, scene transitions, complex cards and edit rules remain planning references, clearly labeled in the UI; they are not silently mapped to a different effect. Word timing is uniform within a layer, not automatic speech alignment.

Agent interface: workflow.py motion-bank, motion-preferences and motion-plan. See skills/sadeq-studio/references/motion-bank.md.


### 0.19.2 — expanded motion references

The local motion bank now includes 100 official v6.0.1 reference demonstrations and posters. The 16 existing native layer effects remain the executable set; 3D, speaker-mask and complex scene references are explicitly labeled in the gallery. Agent guidance now connects the requested feeling to restrained or emphasized moments and checks complete speech, Arabic readability and actual output before delivery. No project data is bundled. See motion-bank/SOURCE.json for the pinned release and archive checksum.
