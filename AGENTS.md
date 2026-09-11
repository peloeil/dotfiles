# AGENTS.md

自分の Linux x86_64 環境を管理する chezmoi の source repository。
復元・運用手順は [README.md](README.md) に置く。このファイルは、変更箇所と検証方法を判断するための案内とする。

## 編集する場所

このリポジトリ内のソースを編集する。target path から対応を調べる場合は `chezmoi source-path <target-path>` を使う。
`chezmoi edit <target-path>` でも同じソースを編集できる。

ファイル名には [chezmoi の属性](https://www.chezmoi.io/reference/source-state-attributes/)が含まれる。

| 属性 | 配置時の意味 |
| --- | --- |
| `dot_` | 先頭の `.` に変換する |
| `private_` | 所有者以外の権限を外す。内容は暗号化されない |
| `executable_` | 実行権限を付ける |
| `symlink_` | ファイル内容をリンク先とするシンボリックリンクを作る |
| `.tmpl` | テンプレートを展開し、拡張子を外す |
| `encrypted_*.age` | age で暗号化したソースを復号して配置する |

| 変更対象 | 主なソース |
| --- | --- |
| 初期入力・age・chezmoi のエディタ | `.chezmoi.toml.tmpl` |
| OS パッケージ・導入処理 | `.chezmoiscripts/` |
| 開発ツール・ランタイム | `dot_config/mise/config.toml` |
| シェル・PATH・fish plugins | `dot_bashrc`、`dot_bash_profile`、`dot_config/private_fish/` |
| Git・研究用メールの切り替え | `dot_config/git/` |
| Neovim・dpp・LSP | `dot_config/nvim/`、`dot_config/clangd/config.yaml` |
| Xorg・i3・表示・入力 | `dot_xinitrc`、`dot_xprofile`、`dot_config/{i3,polybar,picom,alacritty,private_fcitx5}/` |
| Codex のグローバル指示 | `dot_codex/AGENTS.md.tmpl` |
| Claude Code・共通スキル・Ponytail | `dot_claude/`、`dot_agents/skills/`、`dot_config/ponytail/config.json` |
| Podman・Claude のコンテナ実行 | `dot_config/containers/`、`dot_local/bin/executable_claude-sandbox`、`dot_local/share/claude-sandbox/Dockerfile` |
| Sunshine | `dot_config/sunshine/sunshine.conf` |

ルートの `AGENTS.md`、`README.md`、`tests/` は `.chezmoiignore` で配布対象外。
`dot_codex/AGENTS.md.tmpl` はホームの `~/.codex/AGENTS.md` に配布される別のファイル。

## セットアップの依存関係

`init` は `.chezmoi.toml.tmpl` から設定を生成する。
`apply` はテンプレートを評価した後、before scripts、dotfiles の配置、after scripts の順に進む。詳細は [chezmoi の適用順序](https://www.chezmoi.io/reference/application-order/)を参照する。

以下のスクリプトはすべて `.chezmoiscripts/` にある。

| 段階 | ソース | 処理 |
| --- | --- | --- |
| before | `run_once_before_00_install_prereqs.sh.tmpl` | Linux の OS パッケージ |
| before | `run_once_before_01-install-mise.sh.tmpl` | `~/.local/bin/mise` がなければ導入する |
| after | `run_onchange_after_10_install_mise_tools.sh.tmpl` | `mise install --yes` と `uv python install --default` |
| after | `run_once_after_12_install_codex_standalone.sh.tmpl` | `~/.local/bin` に Codex CLI を導入する |
| after | `run_onchange_after_15_init_rtk.sh` | Codex / Claude Code 向けの rtk 初期化 |
| after | `run_onchange_after_20_install_fish_tools.sh.tmpl` | fisher を導入し、`fisher update` |
| after | `run_onchange_after_20_install_hack_nerd_font.sh` | 未導入なら Hack Nerd Font を入れる |
| after | `run_onchange_after_25_install_nvim_plugins.sh.tmpl` | headless Neovim で dpp plugins を導入する |
| after | `run_onchange_after_30_install_ai_plugins.sh.tmpl` | CLI の検出後、Ponytail を導入する |

スクリプトを変えるときは、処理内容と再実行条件を一緒に確認する。

- `run_once` は展開後の内容ごとに成功を記録する。同じ内容は再実行されず、未実行の内容に変われば実行される。
- `run_onchange` は前回成功時から展開後の内容が変わると実行される。別ファイルへの依存は自動では追跡しない。
- mise・fish・Neovim のスクリプトは、対応する設定・plugin 一覧のハッシュを含む。依存ファイルを増やすときはハッシュの対象も更新する。
- OS パッケージの `sudo` 不可や AI ツールの未検出によるスキップも正常終了となる。後から依存を揃えるだけでは再実行されない。
- 再実行時にも既存環境を壊さない処理にする。導入済みかどうかはスクリプトの実行時に判定する。テンプレート内の `lookPath` では before scripts の導入結果を参照できない。

再実行条件の詳細は [chezmoi のスクリプト仕様](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/)を参照する。

## 変更時に確認する前提

- 対象は自分の Linux x86_64。mise のインストーラに macOS 分岐があっても、設定全体の macOS 対応を意味しない。
- ホームのパスはテンプレートでは `.chezmoi.homeDir`、シェルでは `$HOME` を使う。i3 と Alacritty にはホスト名 `helium` の分岐がある。
- 研究用メールの設定は `dot_config/git/private_research.config.tmpl`。Git の条件付き include で `researchDir` 配下に適用する。未設定時は `~/workspace/univ/lab/research/` を使う。
- 壁紙、`monitor-hotplug.sh`、Sunshine 本体・user service、Podman の接続先は管理外。起動処理を変更するときは呼び出し先も確認する。
- ツールの追加先は原則 mise の設定。Codex CLI は standalone installer、Python 本体は uv という導入経路を踏まえて変更する。Codex の検出・実行には `~/.local/bin/codex` を使う。
- rtk の Claude Code hook は `dot_claude/settings.json` が管理する。初期化は `--no-patch` を使っている。
- plugin 本体・キャッシュ・認証情報は管理対象に加えない。スキルや plugin 設定は管理できる。
- 秘密情報は `chezmoi add --encrypt <target-path>` で追加する。age identity は `~/.config/chezmoi/key.txt`。秘密鍵や復号結果をソース・ログに残さない。

## 検証

まず Git の差分でソースの変更を確認する。設定・スクリプトを変更した場合は、さらに chezmoi が実際に配置・実行する内容を確認する。

```sh
git diff --check
git diff
chezmoi diff
chezmoi apply --dry-run
chezmoi doctor
```

文書のみの変更は、記載したパス・コマンド・挙動を実装と照合する。mise を変更した場合は `mise doctor`、スクリプトを変更した場合はテンプレート展開後の構文と再実行条件も確認する。
`python3 tests/check_setup.py` は、一時環境でホームパスの展開と導入処理の回帰を確認する。実際のインストールやデスクトップの起動は行わない。
`--dry-run` はスクリプトを実行しないため、新規環境での導入成功を保証する検証ではない。

実環境への適用やインストールは依頼の範囲に含まれる場合に行う。検証結果を報告するときは、今回の変更による問題と既存環境の差分・診断結果を区別する。
復元手順や自動導入の範囲を変えたら、README も更新する。
