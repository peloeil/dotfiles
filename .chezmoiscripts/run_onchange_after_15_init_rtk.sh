#!/bin/sh
set -eu

rtk_path="$("$HOME/.local/bin/mise" which rtk)"

"$rtk_path" init -g --codex
"$rtk_path" init -g --no-patch
