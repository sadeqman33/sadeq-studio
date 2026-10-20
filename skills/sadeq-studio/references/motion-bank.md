# Motion bank — Studio 0.19.2

Use the configured runtime and existing project. `python3 workflow.py motion-bank` returns 100 catalog entries, native_types, preferences and recent plans. The source catalog/previews are MIT-licensed Majed Video 6.0.1, pinned in motion-bank/SOURCE.json; Studio does not execute its production scripts.

The editor's **بنك الحركات** button opens the local gallery. Users can search/filter, watch reference demonstrations, test native Studio adaptations, prefer/exclude, plan and explicitly apply to selected unlocked text/image/icon layers. Application preserves x/y, width, font, text and timing; sets a 0.7s entrance and 0.24s fade exit and stays undoable until saved normally. `bankMotion` is optional and absent from all legacy layers. Remove it to return to regular motion.

Only IDs with nonempty `native_types` can be submitted in `bankMotion`. There are 16 text effects and six of these also support images/icons. `caption`, `focus`, `wordSwap`, `typewriter` use uniform within-layer timing, not ASR alignment. Do not apply invented numbers: counter animates an existing unambiguous number only. Arabic words stay joined. Preview, Remotion and Hyperframes use one deterministic implementation. The gallery reference video is the upstream demonstration, not a claim of pixel-identical native output; use the Studio demo for the latter.

Transitions, camera, complex cards and edit rules are reference/planning entries, not implemented timeline effects. Never claim all 100 can be exported. J-cuts, match cuts, speed ramps, multi-scene transitions and data cards need separate editing support.

Preferences persist locally across projects. `python3 workflow.py motion-preferences --revision REV --on riseUp blurIn --off glitch` replaces both lists under revision guard. Omit nothing you intend to preserve. No timeline mutation occurs.

`python3 workflow.py motion-plan --project PROJECT_ID --family auto --cue emphasis --native-only` saves a proposal scoped to the active work, respecting exclusions and avoiding recent core selections when alternatives exist. Full reference planning omits --native-only. Plans do not apply edits. Inspect the returned IDs and native_types before building layers. Work/context includes preferences and recent project plans; shared history is limited to 100 plans. Do not change existing videos solely to test the bank.


## Planning with the expanded bank

Choose effects from the requested feeling and saved identity, not from a quota. For an energetic reel, propose up to two or three meaningful emphasis moments with exact timestamps and available assets. For a calm explanation, use plain/fade text and restrained motion; do not add bouncing captions by default. Keep recorded speech complete when shortening pauses and check the final word and tail by listening.

New catalog items 51–100 include Arabic lettering, speaker cutouts, device scenes, data graphics and transitions. These are references, not new `bankMotion` values. Read native_types before proposing an executable plan. Do not pass upstream fields such as capStill, zoomB or bar to Studio. A reference plan must name the missing asset/engine operation instead of pretending a text preset implements it. Preserve readable Arabic words and inspect descenders/diacritics and face-safe placement in the actual output. Project copy always comes from verified context/transcripts, not demo catalog text.

Before delivery, verify a playable nonempty export with expected video stream, dimensions, fps, duration and audible complete speech where present. Review representative frames, including every emphasized moment and the ending. If the user's requirement needs an unconnected effect, explain that limitation before calling the work complete.
