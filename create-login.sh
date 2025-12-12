#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <logins-file>"
  exit 1
fi

logins_file="$1"
source_mp3="mp3/blast"

if [[ ! -d "$source_mp3" ]]; then
  echo "Source folder '$source_mp3' not found"
  exit 1
fi

while IFS= read -r login || [[ -n "$login" ]]; do
  [[ -z "$login" ]] && continue

  echo "Processing '$login'"

  mkdir -p custom
  cat > "custom/${login}.json" <<EOF
{
    "welcome": {
        "mp3": "${login}/in"
    },
    "goodbye": {
        "mp3": "${login}/out"
    }
}
EOF

  target_mp3="mp3/${login}"
  rm -rf "$target_mp3"
  mkdir -p "$target_mp3"
  cp -a "${source_mp3}/." "$target_mp3/"
done < "$logins_file"