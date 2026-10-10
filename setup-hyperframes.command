#!/bin/zsh
cd "${0:A:h}"
studio_node="${SADEQ_NODE:-$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node}"
if [[ ! -x "$studio_node" ]]; then studio_node="$(command -v node)"; fi
export PATH="${studio_node:h}:$PATH"
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_AUTO_INSTALL=1
npm ci || exit 1
"$studio_node" node_modules/hyperframes/dist/cli.js browser ensure
