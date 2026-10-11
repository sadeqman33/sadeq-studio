# What to take from each video

Resolve the project and inventory metadata: file/asset ID, source fingerprint, dimensions/orientation, duration, audio presence, analysis status and source-time coordinates. Original media stays read-only.

For a new project, analyze the whole linked library once; for an initialized project, selected new/changed sources only. Cached analysis samples chronological stills and applies local ASR to the full audio. Reuse unchanged records and mark failed/stale sources. For more than 12 candidate assets, inspect in context batches rather than exceed a plan's selection limit.

Extract and keep distinct:

- Content: what is visibly happening, subject/product/location and possible use, with file/time evidence.
- Visual identity: observed palette, framing, composition, readable typography, logo/existing overlays and contrast. Motion/cut rhythm requires viewing timed segments; don't infer it from a thumbnail.
- Visible text: what is seen at each source time, separately from speech. Do not treat a promotional statement as independent proof.
- Speech: original automatic segments and word source-times, language/dialect when supported, uncertainty and possible repeats/restarts. Verify important names, numbers, negatives and claims by listening when tools allow. Silence/music can produce ASR hallucinations.
- Useful shot ranges: coherent sentences, clear demonstrations, opening/reveal candidates, continuity and obstacles to overlay placement. These are editorial selections, not guaranteed viral shots.
- Project knowledge: evidenced purpose/audience/offers, shared visual habits, contradictions and missing facts. A folder name alone establishes none of these.

The runtime report fields are summary, topics, visual_style, visible_text, speech_notes and uncertainties. Preserve its schema; the richer editorial brief can live in the calling chat/project notes with provenance. Evidence records expose cached_record, stale and source_fingerprint. Inspect the actual relevant images before saying what a frame shows. TXT/SRT from the library retain source times, not timeline-relative times.

After analysis, retrieve fresh context. Respect pinned user knowledge; distinguish observed content, supplied fact, unreviewed ASR and proposed copy. Save reusable approved knowledge in the project's Markdown/JSON memory, not a brand-global skill. No inferred feature, warranty, quote or emotional delivery from filenames alone.
