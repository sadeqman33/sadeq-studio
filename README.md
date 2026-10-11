# Sadeq Studio

**By Sadeq Ammar · صادق ستوديو**

A local video workflow for Codex: describe the project, style and feeling in a chat; the agent uses saved project knowledge to create an editable video. Open that video's own timeline, make small changes by hand, then export MP4.

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

Our fixed React composition converts your independent timeline into local footage sequences and Arabic overlays. It shares the editor's deterministic text motion. Source trims/audio and mute stay in the local FFmpeg pipeline; imported voice/music are mixed afterwards. Editable JSON, React input props and render logs remain with each local export. Timings round cumulative boundaries to 30 fps (at most half a frame at a boundary); clips shorter than one frame are rejected. No arbitrary agent-written JSX, cloud rendering or generated footage is connected.

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

The standard supported path is real source footage → saved identity/evidence → coherent source trims → editable timed text/image/icon layers → independent editable work → MP4. Mode skills explicitly identify limits: generated 3D/collage scenes, word-level karaoke, multicamera/face tracking, a native DaVinci bridge and an automatic Lahajati API are not connected. Imported cover art can be a timed image layer; automatic cover generation/full-frame insertion is not connected. Including an instruction skill does not create those renderer features.

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
