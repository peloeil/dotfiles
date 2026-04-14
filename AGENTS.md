# AGENTS

このファイルは、このリポジトリを触る Codex / エージェント向けの内部メモ。
人間向けの復元手順は `README.md` にだけ書く。README は短く保つ。

## 基本方針

- この repo の主目的は、新しいマシンで開発環境を復元すること。
- ユーザー向け README には、セットアップ手順と普段使うコマンドだけ残す。
- 依存関係の説明、実装の地図、内部挙動の説明は `AGENTS.md` に置く。
- dotfiles の編集は、原則 `chezmoi edit <target-path>` で行う前提。

## 想定環境

- 主対象は Linux デスクトップ。
- `mise` の導入自体は Linux / macOS に対応している。
- i3、polybar、picom、fcitx5、Xorg まわりは Linux 前提。

## 初回セットアップの流れ

`chezmoi init --apply peloeil` で次が走る。

1. `.chezmoi.toml.tmpl` で `email` `name` `machine_type` を prompt。
2. `run_once_before_00_install_prereqs.sh.tmpl` で Linux の前提パッケージを導入。
3. `run_once_before_01-install-mise.sh.tmpl` で `mise` を導入。
4. dotfiles を展開。
5. `run_onchange_after_10_install_mise_tools.sh.tmpl` で `mise install --yes` を実行。
6. fish とフォントの onchange スクリプトを必要に応じて実行。

## 重要ファイル

- `.chezmoi.toml.tmpl`
  `email` `name` `machine_type` の prompt と `chezmoi edit` の既定エディタ。

- `.chezmoiscripts/run_once_before_00_install_prereqs.sh.tmpl`
  Linux の前提パッケージ導入。`apt-get` `pacman` `emerge` を検出して分岐する。

- `.chezmoiscripts/run_once_before_01-install-mise.sh.tmpl`
  `mise` 未導入時にインストールする。

- `.chezmoiscripts/run_onchange_after_10_install_mise_tools.sh.tmpl`
  `mise install --yes` と `uv python install --default` を実行する。README に「シェル再起動で入る」とは書かない。

- `.chezmoiscripts/run_onchange_after_00-install-fish-tools.fish.tmpl`
  `fisher` の導入と `fisher update`。

- `.chezmoiscripts/run_onchange_after_20_install_hack_nerd_font.sh`
  Hack Nerd Font をユーザー領域に導入して `fc-cache` を更新する。

- `dot_config/mise/config.toml`
  開発ツールとランタイムの宣言的な一覧。ツール追加時はまずここを見る。

- `dot_config/private_fish/config.fish`
  シェル初期化。`mise activate fish` もここ。

- `dot_config/git/private_config.tmpl`
  Git のユーザー情報と共通設定。

- `dot_config/nvim/`
  Neovim 設定本体。

- `dot_config/i3/config.tmpl`
  i3 の起動コマンド、キー割り当て、常駐アプリ。

- `dot_xprofile.tmpl`
  fcitx / picom / touchpad 設定。

## 実装上の注意

- `machine_type` は現在 prompt されるが、実際の分岐ではほぼ未使用。必要になったら参照先を増やす。
- README は `.chezmoiignore` で配布対象から外れている。
- repo 直下のパスは `chezmoi` ソース名であり、実ファイル名とは一致しないことがある。必要なら target path と source path を対応づけて説明する。
- セットアップ説明では、実装されていない自動化を README に書かない。

## 変更時の確認

- `chezmoi diff`
- `chezmoi apply --dry-run`
- `chezmoi doctor`
- 必要なら `mise doctor`

README を更新するときは、「久しぶりの新規マシンセットアップ時に README だけで困らないか」を基準にする。
