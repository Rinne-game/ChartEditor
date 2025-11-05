cd src
pwd
ls
pyinstaller ChartEditor.spec \
  --distpath ../build/mac \
  --workpath ../build/mac/temp \