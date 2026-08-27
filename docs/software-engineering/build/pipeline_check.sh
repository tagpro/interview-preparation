#!/usr/bin/env bash
# The three passes each splice a block in ahead of the next marker, and they run
# over the same files in sequence. That composition has to reach a fixed point,
# or every rebuild quietly grows the file. This runs the whole pipeline twice in
# a scratch copy and asserts the second run changes nothing.
#
#     ./pipeline_check.sh
set -euo pipefail
cd "$(dirname "$0")"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp *.html *.py *.mjs *.css "$work/" 2>/dev/null
ln -s "$PWD/node_modules" "$work/node_modules"
cd "$work"

run() {
  for b in build_go build_py build_java build_aws; do python3 "$b.py" >/dev/null; done
  node hl_inject.mjs   >/dev/null
  node print_inject.mjs >/dev/null
  python3 gloss_inject.py >/dev/null
  md5sum backend-go-ladder.html pillar-a-foundations.html pillar-b-go.html \
         pillar-c-cloud.html python-foundations.html java-spring.html \
         aws-deep-dive.html | md5sum | cut -d' ' -f1
}

a=$(run); b=$(run)
echo "first run   $a"
echo "second run  $b"
if [ "$a" = "$b" ]; then echo -e "\nFIXED POINT"; else echo -e "\nPIPELINE DOES NOT CONVERGE"; exit 1; fi
