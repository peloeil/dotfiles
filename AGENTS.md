# AGENTS

このリポジトリを変更する Codex / エージェント向けの内部メモ。
人間向けの復元手順は `README.md` に置き、ここには実装の地図と変更時の制約だけを書く。

## 目的と対象

- 目的は、新しいマシンに開発環境を再現すること。
- 主対象は Linux デスクトップ。i3、polybar、picom、fcitx5、Xorg は Linux 専用。
- `mise` の導入スクリプトだけは Linux / macOS に対応する。
- dotfiles は原則として `chezmoi edit <target-path>` で編集する。

## 初回セットアップ

`chezmoi init --apply peloeil` では、次の順に処理される。

| 順 | ソース | 処理 |
| --- | --- | --- |
| 1 | `.chezmoi.toml.tmpl` | Git の `email`、`researchEmail`、`name` を取得し、age とエディタを設定する |
| 2 | `.chezmoiscripts/run_once_before_00_install_prereqs.sh.tmpl` | Linux で `apt-get`、`pacman`、`emerge` のいずれかを使って前提パッケージを入れる |
| 3 | `.chezmoiscripts/run_once_before_01-install-mise.sh.tmpl` | 未導入なら `mise` を入れる |
| 4 | dotfiles | target path へ展開する |
| 5 | `.chezmoiscripts/run_onchange_after_10_install_mise_tools.sh.tmpl` | `mise install --yes` と `uv python install --default` を実行する |
| 6 | `.chezmoiscripts/run_onchange_after_15_init_rtk.sh` | Codex / Claude Code 用のグローバル instructions を生成する |
| 7 | `.chezmoiscripts/run_onchange_after_20_*` | fisher と fish plugins、Hack Nerd Font を入れる |
| 8 | `.chezmoiscripts/run_onchange_after_25_install_nvim_plugins.sh.tmpl` | headless Neovim で dpp の plugin installer を実行する |
| 9 | `.chezmoiscripts/run_onchange_after_30_install_ai_plugins.sh.tmpl` | Codex / Claude Code に Ponytail plugin を入れる |

前提パッケージの処理は sudo が使えなくてもセットアップを止めない。ただし `run_once` なので、後から sudo が使えるようになっても通常の `chezmoi apply` では再実行されない。

rtk の Claude Code hook は `dot_claude/settings.json` で管理する。したがって rtk の初期化では `--no-patch` を使う。Ponytail の plugin 本体と取得キャッシュは管理対象にしない。

## 設定の所在

| ソース | 内容 |
| --- | --- |
| `dot_config/mise/config.toml` | 開発ツールとランタイム。ツールの追加・削除はまずここで行う |
| `dot_config/private_fish/config.fish` | shell 初期化、環境変数、`mise activate fish` |
| `dot_config/private_fish/fish_plugins` | fisher が同期する plugin 一覧 |
| `dot_config/git/private_config.tmpl` | Git のユーザー情報と共通設定 |
| `dot_config/clangd/config.yaml` | clang-tidy と C / C++ header fallback |
| `dot_config/nvim/` | Neovim 設定 |
| `dot_config/i3/config.tmpl` | i3 の起動処理、キー割り当て、常駐アプリ |
| `dot_xprofile.tmpl` | fcitx、picom、touchpad の設定 |
| `dot_claude/settings.json` | Claude Code の権限、plugin、rtk hook |

## シークレット

- シークレットは `chezmoi add --encrypt <path>` で追加する。
- ソース名は `encrypted_` prefix、拡張子は `.age`。
- age identity は `~/.config/chezmoi/key.txt`。秘密鍵は絶対にリポジトリへ入れない。
- age recipient は `.chezmoi.toml.tmpl` に置いてよい。

## 変更時のルール

- リポジトリ内の名前は chezmoi の source path。実際の target path と一致しない場合がある。
- `README.md` は `.chezmoiignore` で配布対象外。セットアップ手順と普段使うコマンドだけを載せる。
- README に未実装の自動化や「シェル再起動でツールが入る」といった説明を書かない。
- スクリプトは再実行時にも安全になるよう保つ。`run_once` と `run_onchange` の変更は実行タイミングも確認する。

## 確認

```sh
chezmoi diff
chezmoi apply --dry-run
chezmoi doctor
mise doctor  # mise を変更した場合
```

README を変更するときは、久しぶりの新規マシンでも README だけで復元できるかを基準にする。
