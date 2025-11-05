#!/bin/bash
# ===============================
# Mac用ビルド
# ===============================

cd src

pyinstaller main.py \
  --windowed \
  --name "ChartEditor" \
  --osx-bundle-identifier "com.rinnegames.charteditor" \
  --version-file Info.plist \
  --distpath ../build/mac \
  --workpath ../build/mac/temp \
  --specpath ../build/mac

# cd "$(dirname /path/to/example.txt)"
# cp Info.plist ../build/mac/ChartEditor.app/Contents/Info.plist

echo "Macビルド完了"
