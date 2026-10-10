# Repository inspection and adaptation — 2026-10-10

All three were inspected as source references. No explicit repository license was returned by GitHub metadata; no third-party source code, weights, dependencies or training dataset has been incorporated in the runtime/package. Implementation is original. Local research downloads are inspection references, excluded from the built plugin.

## juanls1/TikTok-Virality-Predictor

Source: https://github.com/juanls1/TikTok-Virality-Predictor
Inspected commit: eaf9df1ced9189995731ca413c18e3d782be5470.
Key files: README.md; src/streamlit/app.py; src/utils/utils_streamlit.py; src/audio/audio_utils.py; src/image/image_utils.py; src/text/text_utils.py.

Useful: separate text/audio/image inputs, bounded frame extraction, a multimodal review flow and feedback from measured results. The app uses a views/likes/comments/shares target and fixed independent weights 0.45 text / 0.45 audio / 0.10 image; predictions are denormalized to its dataset range. Its audio language fallback includes en-EN and invokes Google's speech recognition. These conventions are not Iraq-specific validation and are not transferred. We retain modality/evidence separation, explicit unknown speech and local review plus measured outcome logs.

## harbarex/tiktok-virality-prediction

Source: https://github.com/harbarex/tiktok-virality-prediction
Inspected commit: dd600394cbd60562845dcd47fbef067a899ba96a.
Key files: README.md; ViViT/train.py; ViViT/module.py; ViViT/vivit_audio.py.

Useful: temporal video-frame sequences, rather than treating a single thumbnail as the whole video. The README references a top-1000-trending-video dataset and a 2021 university course project. train.py references unavailable Colab/Drive paths, imports a utils module absent from the listed repository tree, and splits a mini-batch randomly at 80/20. We do not install/run its training or call it an Iraqi model. We adopt bounded chronological storyboard samples; a future trained model would need representative negatives plus creator/project and chronological holdouts.

## danilobatson/ai-viral-prediction-tool

Source: https://github.com/danilobatson/ai-viral-prediction-tool
Inspected commit: 60a9da28d78a76760ebb9f4db77b1a9ab687494d.
Key files: pages/api/analyze-stream.js; components/ViralPredictor/index.js; lib/mcp-client.js; README.md.

Useful: progress messages, structured reasoning/recommendations and explanatory dimensions such as practical value and shareability. The API requests an LLM-generated 0–85 viralProbability, 0–100 confidence and optimal posting timing; it has fallback values and uses Twitter/X creator lookup. That code provides no demonstrated calibration for those probability/confidence/timing values. We do not copy its probability, reach forecast, creator lookup, external service integration or simulated delay. We retain transparent evidence, progress and actionable fixes using the existing Codex model.

## What is implemented in Studio v0.2

A new Iraqi-market review panel, original weighted rubric with unknown criteria and coverage, timed edits, distinct hook proposals, current-version fingerprint/stale checks, limited chronological frame samples and local technical audio measurements. Manually supplied outcomes are normalized descriptively and separated by project/platform/distribution/objective/audience/location/measurement age. No trained prediction, trend feed or live account-data integration is claimed.
