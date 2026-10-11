---
name: timeline-edit
description: "Build or revise the exact independent Sadeq Studio video timeline from source-time ranges, independent overlay layers and fresh conflict tokens, then open it for manual edits."
---

# Editable timeline

Read [the execution contract](../sadeq-studio/references/execution.md) first to resolve the existing runtime/project and preserve independent works. Read the relevant source context before proposing edits. Read [timeline-plan.md](../sadeq-studio/references/timeline-plan.md), its plan.schema.json and styles.md. Use actual selected assets and fresh revision/edit/source tokens. One NEW requested video is one separate work; an explicit revision carries the exact already-open work_id. Never combine all project videos/library assets on one timeline.

Translate each coherent source range into supported clip fields. Build new editable copy/images/icons in layers, with global timing and project overlay_assets IDs; leave clips.text empty. Preserve existing manual layers on revisions. Verify total duration, source bounds, contiguous speech and the distinction between source, clip-relative legacy captions and global layer times. Keep the creative choices explained in reason. Save through submit; request render only when within the task. A stale-token refusal requires fresh context and reconciliation, not a force-write.

Return the explicit project+work editor_url. Preview sits immediately above the timeline. Every independent layer has its own lane. The user can fix text, font/color/size, timing and placement, drag layers inside the preview or on the timeline, hide/reorder/duplicate/delete them, scrub, split (S), duplicate/reorder/trim, select presets, save and export without messaging the agent for every minor adjustment. Undo/history are scoped to that work. Do not imply that display tracks support arbitrary overlapping video layers.

For requested selfie blur/color follow the shared cutout operation with the exact clip/work/base token; review results and source lineage, then fresh context. Manual video changes are not automatic project memory lessons.

Use the Caption panel and global word/phrase layers for requested small edits. For recorded speech, use cached source word times via caption-suggest; transcribe locally first if missing. Phrase-to-word splitting is only approximate timing and must be labeled that way. Layer split/delete changes an interval, not recorded dialogue. Text already burned into source pixels is not an editable caption. Import a standalone local video when requested, preserve originals and keep it in the intended work. Set export_settings for requested 1080/4K and 30/60 fps; do not claim optical-flow motion or recovered source detail.

Manual editor shortcuts: Backspace/Delete removes the selected layer or clip from the draft; ⌘Z/Ctrl+Z undoes unsaved manual edits; ⌘⇧Z/Ctrl+Shift+Z (also Ctrl+Y) redoes; ⌘S/Ctrl+S saves; Space plays; S splits. Typing fields keep native text deletion/undo. Session edit history is scoped to the current work; saved history remains available after reloading. The original source file is never deleted.

Shift-click (also Command/Ctrl-click) selects independent layers in the timeline, caption list or preview. Move their shared centre with Group X/Y or drag a selected preview layer; Group Size scales text fonts, image/icon widths and relative spacing together within supported limits. Delete removes all selected layers and Undo restores them. Clip selections stay individual.
