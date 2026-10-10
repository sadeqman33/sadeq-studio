#!/bin/zsh
set -e
cd "${0:A:h}"
studio_node="${SADEQ_NODE:-$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node}"
if [[ ! -x "$studio_node" ]]; then studio_node="$(command -v node)"; fi
export PATH="${studio_node:h}:$PATH"
npm ci
print 'Remotion جاهز. يستخدم Chrome المحلي، أو ينزّل متصفح Remotion عند أول تصدير.'
