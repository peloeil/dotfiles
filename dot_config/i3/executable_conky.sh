#!/bin/sh

killall -q conky
while pgrep -x conky >/dev/null; do
  sleep 1
done

conky --daemonize -c "$HOME/.config/conky/conky.conf"
