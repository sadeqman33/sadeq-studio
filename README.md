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
- Arabic text, local fonts, clip trims/order/mute, timed text and three text motion modes.
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

The repository includes its own plugin manifests and `skills/sadeq-studio/SKILL.md`. Load this directory through your local Codex plugin workflow. A separately copied skill needs the location of this checkout; it must not start an empty second registry while another studio is active.

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

- Sequential clip editing with one text overlay per clip, not a full multitrack nonlinear editor.
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
