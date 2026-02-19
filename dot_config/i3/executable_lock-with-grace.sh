#!/usr/bin/env sh
set -eu

# Give a short grace window after screen blanking.
# If user activity occurs, xss-lock terminates this script before i3lock runs.
grace_seconds="${LOCK_GRACE_SECONDS:-2}"

# Lock immediately for suspend/hibernate requests.
if [ -n "${XSS_SLEEP_LOCK_FD:-}" ]; then
  exec i3lock --nofork
fi

sleep "$grace_seconds"
exec i3lock --nofork
