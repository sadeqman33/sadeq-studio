# Export and observable review

After submitting an authorized draft, use export --project ID or submit --plan-file PATH --render. Verify the intended active work before export. status --project ID is the source of truth for running/error/output; preserve each prior export. Do not label a work from another active ID as this result.

Inspect the produced MP4 with ffprobe for duration, dimensions/frame rate and intended audio. Inspect overlapping text/image/icon layers, font/placement/stacking, enabled state and exact global intervals; Basic export refuses independent layers. Inspect opening/hold/exit states, clip boundaries, readable Arabic/Latin numbers and safe placement. Review representative motion/audio segments using tools that actually support playback/listening. A still screenshot or track presence cannot prove audio intelligibility or synchronization. State a material review gap candidly.

Check requested feeling, coherence, identity and complete speech, especially dropped takes and conjunctions/negation/price cuts. Inspect the export instead of claiming preview guarantees the encoded result. If the timed text appears at a different time, fix the plan using fresh work tokens and rerender to a new version. Do not keep broadening checks after the affected boundaries pass.

Return actual local MP4 with a native preview/link and editor_url containing both project/work IDs. The user edits layer copy, font/color/size, timing, placement/stacking and clip trim/order and available sound controls manually, then exports. Saving the editable draft and encoding the MP4 are separate outcomes. No publication, account mutation, media upload or charges are implied by producing a file.

## Output settings

Each independent work saves export_settings: resolution 1080/4k and fps 30/60. Both pinned local engines render the chosen dimensions and frame cadence; server verifies the actual encoded dimensions/fps/duration before reporting success. Portrait 4K is 2160×3840; landscape UHD is 3840×2160. Remotion rounds cumulative boundaries at the selected fps and requires at least one frame per clip. Text geometry/font sizes scale with the output. The basic renderer remains 720p/30 and refuses 4K/60.

4K/60 takes more time/storage than 1080/30. Upscaling low-resolution footage cannot recover recorded detail; rendering 60fps does not invent new camera motion from 30fps footage. Graphics render at the selected fps. No optical-flow interpolation or AI upscaler is connected. Preserve the independent editable work regardless of export quality.
