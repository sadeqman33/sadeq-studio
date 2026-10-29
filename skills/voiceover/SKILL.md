---
name: voiceover
description: "Prepare project-aware Iraqi narration and delivery notes for Sadeq Studio, using local VoiceStudio/VoxCPM2 generation and audio import and preserving source audio decisions."
---

# Voice-over

Read [the execution contract](../sadeq-studio/references/execution.md) first to resolve the existing runtime/project and preserve independent works. Read the relevant source context before proposing edits. Read saved voiceover preferences, project voice/style and verified current facts. Draft natural Iraqi copy matching the desired feeling and footage timing. Keep spoken dialogue transcription separate from proposed narration. Identify actual pauses/emphasis and pronunciation of names/numbers; don't invent testimonials, course promises or product claims.

VoiceStudio is the user's chosen provider; never route narration to Lahajati or another hosted provider. Read [voicestudio.md](../sadeq-studio/references/voicestudio.md). `workflow.py voice-status` checks the running local service and selected, installed VoxCPM2-8bit model. Use only discovered saved profile IDs or the model's synthetic default, not a person's name masquerading as a profile. Default Arabic is supported; an Iraqi accent is not guaranteed and needs listening. Voice cloning requires an authorized reference, never infer consent from finding a recording.

Write the proposed script in this chat or use workflow.py voice-script --project ID --brief-file PATH when requested. Save/review the intended text in the exact work. `workflow.py voice-generate --project ID` uses that work's saved text, dialect, voice description, direction and voiceProfile, with fresh work/fingerprint guards. The editor has Check VoiceStudio, a voice selector, Generate and a standalone audio player. Generation is explicit; never start it on project open. Check job completion and the actual audio before claiming success. No provider fallback, model installation, engine switching or remote requests happen during Studio generation.

Changing text cannot change an existing recording. After actual import inspect timing/gain and the original audio policy; avoid duplicated competing narration or muting source speech without the requested intent. Render through export-video and verify intended audio with available listening tools. No uploads, account changes or paid generation are implied by writing a script.
