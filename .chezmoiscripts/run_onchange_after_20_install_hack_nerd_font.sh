#!/bin/sh
set -eu

font_name="Hack Nerd Font"
font_dir="${XDG_DATA_HOME:-"$HOME/.local/share"}/fonts"
release_url="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/Hack.zip"

mkdir -p "$font_dir"

if find "$font_dir" -maxdepth 1 -type f -name "HackNerdFont*.ttf" | grep -q .; then
  echo "$font_name already installed in $font_dir."
  exit 0
fi

tmp_dir=$(mktemp -d)
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

zip_path="$tmp_dir/Hack.zip"

if command -v curl >/dev/null 2>&1; then
  curl -fLo "$zip_path" "$release_url"
elif command -v wget >/dev/null 2>&1; then
  wget -O "$zip_path" "$release_url"
else
  echo "Neither curl nor wget is available to download $font_name." >&2
  exit 1
fi

extract_zip() {
  archive="$1"
  destination="$2"

  if command -v unzip >/dev/null 2>&1; then
    unzip -q "$archive" -d "$destination"
  elif command -v bsdtar >/dev/null 2>&1; then
    bsdtar -xf "$archive" -C "$destination"
  elif command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import sys
import zipfile
from pathlib import Path

a, dest = sys.argv[1], Path(sys.argv[2])
dest.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(a) as zf:
    zf.extractall(dest)
PY
  else
    echo "No tool available to extract $font_name archive." >&2
    exit 1
  fi
}

extract_zip "$zip_path" "$tmp_dir"

font_files_found=false
for font_file in "$tmp_dir"/HackNerdFont*.ttf; do
  if [ -f "$font_file" ]; then
    install -m644 "$font_file" "$font_dir/"
    font_files_found=true
  fi
done

if [ "$font_files_found" = false ]; then
  echo "No font files found in downloaded archive for $font_name." >&2
  exit 1
fi

if command -v fc-cache >/dev/null 2>&1; then
  fc-cache -f "$font_dir"
else
  echo "fc-cache not found; you may need to refresh font cache manually." >&2
fi

echo "$font_name installed to $font_dir."
