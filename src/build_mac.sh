#!/bin/bash
# ===============================
# Mac用ビルド
# ===============================

cd src

pyinstaller --onefile --noconsole main.py \
--name "TuningLaneEditor" \
--distpath ../build/mac \
--workpath ../build/mac/temp \
--specpath ../build/mac

echo "Macビルド完了"
