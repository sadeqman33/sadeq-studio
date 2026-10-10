#!/bin/zsh
set -e
cd "${0:A:h}"
python3 -m venv .venv-asr
.venv-asr/bin/python -m pip install -r requirements-transcription.txt
.venv-asr/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('mlx-community/whisper-large-v3-turbo', allow_patterns=['config.json','weights.safetensors'])
print('محرك التفريغ المحلي جاهز')
PY
