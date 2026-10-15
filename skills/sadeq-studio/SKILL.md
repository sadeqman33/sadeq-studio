---
name: sadeq-studio
description: "Create an editable video for a saved Sadeq Studio project from a chat brief; route analysis, style, speech, text, timeline and export through the packaged workflows."
---

# Studio workflow

You are the creative agent in this chat; the Studio is the local executor and manual finishing editor. Read [execution.md](references/execution.md) first. Use the user's project, requested feeling and actual assets. Reuse saved knowledge rather than learn the project from scratch every time.

For a motion bank request, read [motion-bank.md](references/motion-bank.md).

## Direct Studio creation

When the user wants to choose options and launch the agent inside Studio, open the **فيديو بالإيجنت** wizard. Its final user-triggered button launches the existing structured agent, creates an independent editable work, and optionally exports locally. Do not launch it merely to demonstrate the UI on real project media. Chat-initiated work still uses the normal calling-chat workflow below. The wizard's motion and caption controls are executable; camera/transition reference previews do not imply implemented camera transforms.

## Route only what this request needs

| Task | Packaged skill |
|---|---|
| New project, identity, purpose, lasting style | [project-memory](../project-memory/SKILL.md) |
| Analyze videos, speech and visible text, find useful shots | [video-analysis](../video-analysis/SKILL.md) |
| Choose coherent best takes, repeats and mistakes | [speech-edit](../speech-edit/SKILL.md) |
| Arabic overlay copy, font, placement, motion | [arabic-product-video](../arabic-product-video/SKILL.md) |
| Talking/product reel or ad | [video-ad-editor](../video-ad-editor/SKILL.md) |
| Silent/ambient footage montage | [montage-video](../montage-video/SKILL.md) |
| Text motion or an explainer brief | [motion-video](../motion-video/SKILL.md) |
| Episode/interview excerpts | [podcast-video](../podcast-video/SKILL.md) |
| Requested cover/thumbnail | [thumbnail-video](../thumbnail-video/SKILL.md) |
| Explicit DaVinci request | [davinci-video](../davinci-video/SKILL.md) |
| Distinct Meta concepts or testing | [meta-ads-diversity](../meta-ads-diversity/SKILL.md) |
| Iraqi audience/hook review or outcome learning | [iraqi-video-review](../iraqi-video-review/SKILL.md) |
| Build/revise the exact independent timeline | [timeline-edit](../timeline-edit/SKILL.md) |
| Voice-over/Lahajati | [voiceover](../voiceover/SKILL.md) |
| Requested MP4 and delivery checks | [export-video](../export-video/SKILL.md) |

The normal path is saved identity → current source evidence → coherent idea/takes → short accurate copy with independently editable text/image/icon layers and shot-specific placement → independent editable work → requested render → manual finishing. Select applicable skills; don't load every mode or force advertising onto an emotional/noncommercial film. Read [styles.md](references/styles.md) and [capabilities.json](references/capabilities.json) as needed. These are shared instructions, not permission to invoke missing tools.

For a requested video, finish the supported executable path through actual export; don't stop at a script/plan. If the exact brief requires an unconnected capability, disclose the specific gap instead of silently substituting another kind of deliverable. New plugin skills may require a new chat/app refresh to appear in the picker. Invocation is `$sadeq-studio` or the Sadeq Studio plugin.
