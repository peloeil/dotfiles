#!/bin/sh
set -eu

rtk_path="$("$HOME/.local/bin/mise" which rtk)"

# `--codex` rewrites ~/.codex/AGENTS.md with an @RTK.md reference and mode 600.
# That path links to the shared OpenCode instructions, so keep the managed file
# as the source defines it: drop the reference and restore the previous mode.
codex_agents="$HOME/.codex/AGENTS.md"
codex_mode=""
if [ -f "$codex_agents" ]; then
	codex_mode="$(stat -Lc %a "$codex_agents")"
fi

"$rtk_path" init -g --codex

rtk_reference="@$HOME/.codex/RTK.md"
if [ -n "$codex_mode" ] && grep -qxF "$rtk_reference" "$codex_agents"; then
	trimmed="$(mktemp)"
	awk -v reference="$rtk_reference" '
		$0 == reference { next }
		{ lines[++count] = $0 }
		END {
			while (count > 0 && lines[count] == "") count--
			for (i = 1; i <= count; i++) print lines[i]
		}
	' "$codex_agents" >"$trimmed"
	cat "$trimmed" >"$codex_agents"
	rm -f "$trimmed"
	chmod "$codex_mode" "$codex_agents"
fi

"$rtk_path" init -g --opencode --no-patch
