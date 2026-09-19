# dotfiles

自分の Linux x86_64 環境を復元・更新するためのリポジトリ。
chezmoi で設定ファイルを配布し、mise で開発ツールとランタイムを入れる。Codex CLI は standalone installer、Python 本体は uv で導入する。

`full` は Xorg / i3 デスクトップを含む全構成、`minimal` は GUI を省いた開発環境。
どちらも Bash / fish、tmux、Neovim、言語環境、AI ツール、コンテナ用ツールを導入する。
多くのツールに `latest` を指定しているため、復元時のバージョンは導入時点で変わる。

## 新しいマシンに復元する

### 1. 準備する

一般ユーザーで作業する。以下のコマンドは Bash 用。

- ネットワーク接続と `curl`、`git`、`tar` を用意する。
- OS パッケージの自動導入には `sudo` が必要。`apt-get`、`pacman`、`emerge` に分岐する。
- Gentoo の `full` では `app-i18n/mozc` の `fcitx5` USE フラグを有効にする。

暗号化ファイルは現在追跡していない。今後追加した暗号化ファイルも復元する場合は、先に下記の「秘密情報を管理する」に従って鍵を配置する。

### 2. リポジトリを取得する

[chezmoi のインストーラ](https://www.chezmoi.io/install/#one-line-binary-install)を使い、設定を初期化する。

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin" init peloeil
export PATH="$HOME/.local/bin:$PATH"
```

`Install profile` で `full`（既定）か `minimal` を選び、Git の通常用メールアドレス、研究用メールアドレス、研究用ディレクトリ、名前を入力する。
`Start a Denops shared server at login` では [Denops の共有サーバー](#denops-の共有サーバー)を使うか選ぶ。既定は無効。
入力値は `~/.config/chezmoi/chezmoi.toml` に保存される。研究用ディレクトリ配下のリポジトリでは、研究用メールアドレスへ自動で切り替わる。

最初から minimal を指定して取得する場合は、上のインストーラのコマンドを次に置き換える。

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin" \
  init peloeil --promptChoice 'Install profile=minimal'
export PATH="$HOME/.local/bin:$PATH"
```

| 導入対象 | full | minimal |
| --- | --- | --- |
| シェル・Git・tmux・mise・Neovim・言語環境 | あり | あり |
| Codex・Claude Code・rtk・Ponytail・コンテナ用ツール | あり | あり |
| Xorg・i3・Alacritty・fcitx5・デスクトップ用 OS パッケージと設定 | あり | なし |
| Sunshine の設定・Hack Nerd Font の導入・ログイン時の `startx` | あり | なし |

SSH 先で使う場合、Tide などのアイコン表示に必要な Nerd Font は接続元の端末で設定する。

### 3. 確認して適用する

```sh
chezmoi diff
chezmoi apply --dry-run
chezmoi apply
```

`apply` は OS の前提パッケージと mise を導入し、設定ファイルを配置した後、次をセットアップする。

- mise の開発ツールと uv のデフォルト Python
- Codex CLI、rtk のグローバル指示
- fisher / fish plugins、Hack Nerd Font（full のみ）
- Neovim の dpp plugins
- Denops の systemd user service の有効・無効化（user manager がある場合）
- Codex / Claude Code の Ponytail（CLI を検出できた場合）

途中で失敗したら、原因を解消して `chezmoi apply` を再実行する。
`sudo` を使えない場合は OS パッケージの導入をスキップするが、不足パッケージによって後続処理が失敗することはある。スキップした処理の再実行方法は下記を参照する。

完了後は新しい端末を開く。fish を使う場合は `~/.local/bin/mise exec -- fish` で起動できる。ログインシェルの変更は自動では行わない。
Ponytail の既定モードは `~/.config/ponytail/config.json` で `off` にしている。

### 4. マシン固有の設定を整える

以下はこのリポジトリだけでは揃わない。使うものを別途用意する。
minimal ではデスクトップ関連（壁紙・モニター設定・Sunshine）の準備は不要。

| 対象 | 必要な作業 |
| --- | --- |
| 壁紙 | `~/pictures/neko.jpg` を配置するか、i3 の指定を変更する |
| モニター設定 | `~/.config/i3/monitor-hotplug.sh` を用意するか、i3 の起動処理・キー割り当てを変更する |
| Sunshine | 本体と systemd user service を用意し、`~/.config/sunshine/sunshine.conf` の GPU・出力指定を合わせる |
| Podman | 導入される CLI は remote 版。利用先のサービスまたは VM と接続設定を用意する |
| AI ツール | Codex / Claude Code の認証を済ませる |

full の Bash のログイン設定は、SSH 接続ではなく、`DISPLAY` がない `tty1` で `startx` を実行する。`.xinitrc` は fcitx5 などを初期化し、Sunshine の再起動と i3 の起動を行う。

ホスト名が `helium` の場合は、i3 の時間経過による画面消灯を無効にし、Alacritty のフォントサイズを変更する。

## 構成を切り替える

`chezmoi edit-config` で `[data]` の設定を変更し、差分を確認して適用する。

```sh
chezmoi edit-config
chezmoi diff
chezmoi apply --dry-run
chezmoi apply
```

### full / minimal

`profile` を `"full"` または `"minimal"` にする。未設定の既存環境は full として扱う。
minimal から full に切り替えると GUI の設定・導入処理も対象になる。full から minimal に切り替えても、導入済みパッケージや除外した設定ファイルは自動削除しない。ログイン時の `startx` は無効になる。
OS パッケージ導入は `run_once` のため、以前使った構成へ戻しただけでは再実行されない。必要なら下記の「OS パッケージの導入がスキップされた」のコマンドで再実行する。

### Denops の共有サーバー

`denopsSharedServer = true` にすると、`denops-shared-server.service` がログイン時に起動し、Neovim 間で Denops を使い回してファイラーなどの初回応答を早める。systemd user manager が必要。
`false`（既定）に戻して適用すると常駐を停止し、Neovim ごとに Denops を起動する。

接続先は `127.0.0.1:32123`。競合時は `denopsServerPort` でポートを変更できる。
共有サーバーは認証を行わないため、複数人で使うマシンでは無効のまま使う。

## 設定とツールを更新する

管理対象を編集するときは、ホームディレクトリ側のパスを指定する。

```sh
chezmoi edit ~/.config/fish/config.fish
chezmoi diff
chezmoi apply
```

取得済みのソースは `chezmoi cd` で開いて直接編集することもできる。
テンプレート化していない実ファイル側の変更は `chezmoi re-add <target-path>` で取り込める。`.tmpl` の内容はソース側で編集する。

別のマシンでコミット・push した変更は、次で取得して適用する。

```sh
chezmoi update
```

研究用メールは [Git の条件付き include](https://git-scm.com/docs/git-config#_conditional_includes) で自動選択する。対象の既定値は `~/workspace/univ/lab/research/`。場所を変える場合は `chezmoi edit-config` で `[data]` の `researchDir` を絶対パスまたは `~/...` に設定し、`chezmoi apply` する。`researchDir` が未設定の既存環境でも既定の場所を使う。

リポジトリで実際に使われるメールは次で確認できる。個別の `git config --local user.email` があれば、そちらが優先される。

```sh
git config --show-origin --get user.email
```

ツールを追加・変更するときは mise の設定を編集して適用する。設定の変更を検知してインストール処理が再実行される。

```sh
chezmoi edit ~/.config/mise/config.toml
chezmoi apply
```

導入済みツールの更新は `mise upgrade`、不足ツールの再導入は `mise install --yes`、デフォルト Python の導入は `uv python install --default` で行う。作業中のプロジェクトの mise 設定の影響を避けるには、ホームディレクトリで実行する。

Codex CLI の更新はインストーラを再実行する。

```sh
curl -fsSL https://chatgpt.com/codex/install.sh |
  env CODEX_INSTALL_DIR="$HOME/.local/bin" \
      CODEX_NON_INTERACTIVE=1 \
      PATH="$HOME/.local/bin:/usr/bin:/bin" sh
```

## AI の指示とスキル

| 用途 | ソース・配置先 |
| --- | --- |
| このリポジトリの編集上の制約 | [AGENTS.md](AGENTS.md)（配布対象外） |
| Codex 共通の応答方針 | `dot_codex/AGENTS.md.tmpl` → `~/.codex/AGENTS.md` |
| コミットの分割・メッセージ規約 | `dot_agents/skills/commit/SKILL.md` → `~/.agents/skills/commit/SKILL.md` |
| Claude Code からの commit 利用 | `~/.claude/skills/commit` → `~/.agents/skills/commit`（補助資料を含むディレクトリへのシンボリックリンク） |
| Claude Code の設定・rtk hook | `dot_claude/settings.json` → `~/.claude/settings.json` |
| Ponytail の既定モード | `dot_config/ponytail/config.json` → `~/.config/ponytail/config.json` |

plugin 本体・キャッシュ・認証情報はこのリポジトリでは管理しない。

## セットアップの構成

初期入力と age の設定は `.chezmoi.toml.tmpl`、full / minimal の配布範囲は `.chezmoiignore`、開発ツールは `dot_config/mise/config.toml` で管理する。
`init` は設定を生成し、`apply` はテンプレート評価後、before scripts、dotfiles、after scripts の順に処理する。

以下はすべて `.chezmoiscripts/` 内のスクリプト。

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
| after | `run_onchange_after_26_configure_denops_server.sh.tmpl` | 選択した Denops の常駐設定を systemd user service に反映する |
| after | `run_onchange_after_30_install_ai_plugins.sh.tmpl` | CLI の検出後、Ponytail を導入する |

`run_once` は展開後の内容ごとに成功を記録し、`run_onchange` は前回成功時から内容が変わると実行する。mise・fish・Neovim のスクリプトには対応する設定・plugin 一覧のハッシュを含めている。
スキップも成功として記録されるため、依存を後から揃えただけでは再実行されない。詳細は [chezmoi のスクリプト仕様](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/)を参照する。

## セットアップを補完する

### OS パッケージの導入がスキップされた

`sudo` が使える状態にして前提パッケージの処理を再実行し、その後に適用を再開する。

```sh
chezmoi execute-template --file \
  "$(chezmoi source-path)/.chezmoiscripts/run_once_before_00_install_prereqs.sh.tmpl" | sh
chezmoi apply
```

### Denops の共有サーバー設定がスキップされた

systemd user manager が利用可能になってから、設定処理を再実行する。

```sh
chezmoi execute-template --file \
  "$(chezmoi source-path)/.chezmoiscripts/run_onchange_after_26_configure_denops_server.sh.tmpl" | sh
```

### Ponytail の導入がスキップされた

Codex / Claude Code を導入した後、Ponytail の導入処理だけを再実行する。Codex は `~/.local/bin/codex`、Claude Code は `~/.local/bin/mise which claude` で検出できる状態にする。

```sh
chezmoi execute-template --file \
  "$(chezmoi source-path)/.chezmoiscripts/run_onchange_after_30_install_ai_plugins.sh.tmpl" | sh
```

### 状態を確認する

```sh
chezmoi doctor
mise doctor
```

## 秘密情報を管理する

age の公開鍵は `.chezmoi.toml.tmpl`、秘密鍵の参照先は `~/.config/chezmoi/key.txt`。
既存の暗号化ファイルを復元するときは、対応する秘密鍵をバックアップから配置する。

```sh
install -Dm600 /path/to/key.txt ~/.config/chezmoi/key.txt
```

新しく秘密情報を管理する場合は `chezmoi add --encrypt /path/to/secret` を使う。
秘密鍵と暗号化前の内容はコミットしない。鍵のバックアップはリポジトリとは別に保管する。
