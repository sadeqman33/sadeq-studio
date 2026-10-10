# Third-party dependencies

Sadeq Studio original application code is by Sadeq Ammar. Dependencies are separate components and retain their own licenses.

- Hyperframes 0.8.143 — HeyGen/contributors, Apache-2.0. https://github.com/heygen-com/hyperframes . License snapshot: Hyperframes-LICENSE.txt.
- GSAP 3.14.2 — GreenSock/Webflow, Standard no-charge license. https://gsap.com/community/standard-license/ . License snapshot: GSAP-LICENSE.txt.
- Playwright 1.62.1 — Microsoft, Apache-2.0. https://github.com/microsoft/playwright . License snapshot: Playwright-LICENSE.txt. Installed by npm; its distribution retains its notices.
- Remotion 4.0.534 — Remotion AG, special Remotion License. https://github.com/remotion-dev/remotion . License snapshot: Remotion-LICENSE.md. Individuals, qualifying small organizations and evaluation uses are covered by its free tier; other organizations need a company license. This is a dependency used for rendering, not a relicensed framework.
- React / React DOM 19.3.0 — Meta/contributors, MIT; notices are retained in npm distributions.
- Optional speech: MLX Whisper and Silero VAD are installed separately by pip. Model weights are downloaded separately; their licenses remain with their upstream distributions.
- Optional cutout: MediaPipe 0.10.32 (Google/contributors, Apache-2.0), OpenCV contrib 4.11.0.86 (Apache-2.0), NumPy 2.2.6 (BSD-3-Clause). Installed separately from PyPI; their package notices remain intact. MediaPipe license snapshot: MediaPipe-LICENSE.txt. Official SelfieSegmenter float16 version 1 weights are downloaded separately from Google with SHA-256 verification. https://github.com/google-ai-edge/mediapipe and https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter . No private footage is sent to Google.
- Optional PDF reader: pypdf is installed separately by pip and retains its upstream license.

No third-party predictor code, external video workflow scripts, model weights, stock footage, font files or private project data are bundled. Fonts must be installed locally under the user's own license. Render outputs and composition copies remain local and are excluded from Git.
