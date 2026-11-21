#!/bin/sh
# Copies the web build into www/ for the Android app.
#   ./prepare_www.sh ../build/web/drift-tank/build/web
#
# Android's packaging tool treats every "*.gz" file specially: it unzips it and
# drops the ".gz" from the name. The page asks for "drift-tank.tar.gz", which
# would then not exist -> the game hangs on "Loading". So we rename the file to
# something Android leaves alone and point index.html at the new name.
set -e
cd "$(dirname "$0")"
SRC="$1"
rm -rf www
cp -R "$SRC" www
mv www/drift-tank.tar.gz www/drift-tank.tgzdata
rm -f www/drift-tank.apk          # zip copy of the same files, not needed in the app
sed -i.bak 's/drift-tank\.tar\.gz/drift-tank.tgzdata/g' www/index.html && rm www/index.html.bak
grep -q "drift-tank.tgzdata" www/index.html
echo "www/ ready"
