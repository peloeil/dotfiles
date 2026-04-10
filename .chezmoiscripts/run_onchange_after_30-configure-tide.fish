#!/usr/bin/env fish

type -q tide; or exit 0

tide configure --auto \
  --style=Classic \
  --prompt_colors='True color' \
  --classic_prompt_color=Light \
  --show_time=No \
  --classic_prompt_separators=Angled \
  --powerline_prompt_heads=Sharp \
  --powerline_prompt_tails=Slanted \
  --powerline_prompt_style='Two lines, character' \
  --prompt_connection=Solid \
  --powerline_right_prompt_frame=No \
  --prompt_connection_andor_frame_color=Light \
  --prompt_spacing=Sparse \
  --icons='Many icons' \
  --transient=No
