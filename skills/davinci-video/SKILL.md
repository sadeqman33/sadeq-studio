---
name: davinci-video
description: "Handle an explicit DaVinci/Resolve editing request for a Sadeq Studio project, verifying available editor tools and identifying the missing bridge before any timeline claims."
---

# DaVinci handoff

Read [the execution contract](../sadeq-studio/references/execution.md) first to resolve the existing runtime/project and preserve independent works. Read the relevant source context before proposing edits. Only apply when the user explicitly requests Resolve/DaVinci. Inspect available current editor tools and local installation without inventing an MCP endpoint or assuming a version/license supports scripting. Read the installed official scripting documentation or current primary docs when compatibility matters.

Sadeq Studio does not currently ship a DaVinci scripting bridge or native Resolve timeline exporter. Its editable timeline is the local Studio work, not a Resolve project. If verified editor tools exist in this session, use their supported schema with the exact authorized project/timeline, source clips/timecodes, and typography; preserve originals and unrelated timelines. An existing tool connection does not authorize overwriting a different editor project.

If no tools/bridge exist, state the concrete gap and keep the source-range plan and project knowledge usable for a later handoff. Don't silently render an MP4 and call it an editable Resolve timeline. Don't buy a license, install a different edition or claim version-specific restrictions from old unverified skill text. The standard Studio editor remains available for the supported workflow when that fits the user's request.
