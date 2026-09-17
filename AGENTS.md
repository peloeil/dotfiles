# AGENTS.md

自分の Linux x86_64 環境を管理する chezmoi の source repository。
復元・運用は [README.md](README.md)、導入処理の変更は [セットアップの構成](README.md#セットアップの構成)、AI 設定の変更は [AI の指示とスキル](README.md#ai-の指示とスキル) を参照する。

## 編集する場所と制約

- このリポジトリ内のソースを編集する。配置先から調べるには `chezmoi source-path <target-path>` を使う。`dot_`、`private_`、`executable_`、`symlink_`、`.tmpl` は [chezmoi の属性](https://www.chezmoi.io/reference/source-state-attributes/)。`private_` は権限指定であり、暗号化ではない。
- ルートの `AGENTS.md`、`README.md`、`tests/` は配布対象外。`~/.codex/AGENTS.md` のソースは `dot_codex/AGENTS.md.tmpl`。
- ホームのパスはテンプレートでは `.chezmoi.homeDir`、シェルでは `$HOME` を使う。
- `profile` は `full`（未設定時も既定）か `minimal`。配布範囲は `.chezmoiignore`、OS パッケージは前提パッケージのスクリプト、`startx` は Bash のテンプレートに分岐がある。
- ツールの追加先は原則 `dot_config/mise/config.toml`。Codex CLI は standalone installer、Python 本体は uv で導入する。Codex の検出・実行には `~/.local/bin/codex` を使う。
- 壁紙、`monitor-hotplug.sh`、Sunshine 本体・user service、Podman の接続先は管理外。起動処理の変更では [マシン固有の設定](README.md#4-マシン固有の設定を整える) も確認する。
- rtk の Claude Code hook は `dot_claude/settings.json` が管理する。初期化の `--no-patch` を維持する。
- plugin 本体・キャッシュ・認証情報は管理対象に加えない。秘密情報は `chezmoi add --encrypt <target-path>` で追加し、秘密鍵や復号結果をソース・ログに残さない。

## 導入処理を変更するとき

`apply` はテンプレート評価、before scripts、dotfiles の配置、after scripts の順に進む。
導入済みかどうかはスクリプト実行時に判定する。テンプレート内の `lookPath` では before scripts の導入結果を参照できない。

- `run_once` は展開後の内容ごと、`run_onchange` は前回成功時からの内容変更で再実行される。既存環境でも再実行できる処理にする。
- 別ファイルへの依存は自動追跡されない。mise・fish・Neovim の設定や plugin 一覧への依存を増やす場合は、スクリプト内のハッシュ対象も更新する。
- `sudo` 不可や CLI 未検出によるスキップも正常終了として記録される。後から依存を揃えるだけでは再実行されない。

復元手順や自動導入の範囲を変えたら README も更新する。

## 検証と完了条件

変更に応じて次を使う。

| 変更 | 検証 |
| --- | --- |
| 文書・スキル | `git diff --check` と差分確認。記載したパス・コマンド・挙動を実装と照合する |
| 配置する設定・削除対象 | `chezmoi diff`、`chezmoi apply --dry-run` で対象と展開結果を確認する |
| テンプレート・導入処理 | `python3 tests/check_setup.py`。スクリプトは展開後の構文と再実行条件も確認する |
| 環境の診断が必要なとき | `chezmoi doctor`。mise 関連は `mise doctor` |

`tests/check_setup.py` は一時環境とモックを使い、実際のインストールやデスクトップの起動は行わない。変更に必要な検証と、その変更に起因する失敗の修正・再検証まで進める。
`--dry-run` はスクリプトを実行しないため、実際の導入成功を保証しない。
実環境への適用・インストールは依頼の範囲に含まれる場合に行う。完了時は検証結果と未検証事項を示し、既存環境の問題を今回の変更による問題と区別する。
