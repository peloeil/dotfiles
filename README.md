# dotfiles

自分の Linux x86_64 環境を復元・更新するためのリポジトリ。
chezmoi で設定ファイルを配布し、mise で開発ツールとランタイムを入れる。Codex CLI は standalone installer、Python 本体は uv で導入する。

デスクトップは Xorg / i3、シェルは Bash / fish、エディタは Neovim。
多くのツールに `latest` を指定しているため、復元時のバージョンは導入時点で変わる。

## 新しいマシンに復元する

### 1. 準備する

一般ユーザーで作業する。以下のコマンドは Bash 用。

- ネットワーク接続と `curl`、`git`、`tar` を用意する。
- OS パッケージの自動導入には `sudo` が必要。`apt-get`、`pacman`、`emerge` に分岐があり、Arch ではシステム更新も実行する。
- Gentoo では `app-i18n/mozc` の `fcitx5` USE フラグを有効にする。

暗号化ファイルは現在追跡していない。今後追加した暗号化ファイルも復元する場合は、先に下記の「秘密情報を管理する」に従って鍵を配置する。

### 2. リポジトリを取得する

[chezmoi のインストーラ](https://www.chezmoi.io/install/#one-line-binary-install)を使い、設定を初期化する。

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin" init peloeil
export PATH="$HOME/.local/bin:$PATH"
```

Git の通常用メールアドレス、研究用メールアドレス、研究用ディレクトリ、名前を入力する。
入力値は `~/.config/chezmoi/chezmoi.toml` に保存される。研究用ディレクトリ配下のリポジトリでは、研究用メールアドレスへ自動で切り替わる。

### 3. 確認して適用する

```sh
chezmoi diff
chezmoi apply --dry-run
chezmoi apply
```

`apply` は OS の前提パッケージと mise を導入し、設定ファイルを配置した後、次をセットアップする。

- mise の開発ツールと uv のデフォルト Python
- Codex CLI、rtk のグローバル指示
- fisher / fish plugins、Hack Nerd Font
- Neovim の dpp plugins
- Codex / Claude Code の Ponytail（CLI を検出できた場合）

途中で失敗したら、原因を解消して `chezmoi apply` を再実行する。
`sudo` を使えない場合は OS パッケージの導入をスキップするが、不足パッケージによって後続処理が失敗することはある。スキップした処理の再実行方法は下記を参照する。

完了後は新しい端末を開く。fish を使う場合は `~/.local/bin/mise exec -- fish` で起動できる。ログインシェルの変更は自動では行わない。
Ponytail の既定モードは `~/.config/ponytail/config.json` で `off` にしている。

### 4. マシン固有の設定を整える

以下はこのリポジトリだけでは揃わない。使うものを別途用意する。

| 対象 | 必要な作業 |
| --- | --- |
| 壁紙 | `~/pictures/neko.jpg` を配置するか、i3 の指定を変更する |
| モニター設定 | `~/.config/i3/monitor-hotplug.sh` を用意するか、i3 の起動処理・キー割り当てを変更する |
| Sunshine | 本体と systemd user service を用意し、`~/.config/sunshine/sunshine.conf` の GPU・出力指定を合わせる |
| Podman | 導入される CLI は remote 版。利用先のサービスまたは VM と接続設定を用意する |
| AI ツール | Codex / Claude Code の認証を済ませる |

Bash のログイン設定は、SSH 接続ではなく、`DISPLAY` がない `tty1` で `startx` を実行する。`.xinitrc` は fcitx5 などを初期化し、Sunshine の再起動と i3 の起動を行う。

ホスト名が `helium` の場合は、i3 の時間経過による画面消灯を無効にし、Alacritty のフォントサイズを変更する。

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

## セットアップを補完する

### OS パッケージの導入がスキップされた

スキップもスクリプトの正常終了として記録されるため、後から `sudo` が使えるようになっても、同じ内容のスクリプトは通常の `apply` では再実行されない。
前提パッケージの処理だけを実行し、その後に適用を再開する。

```sh
chezmoi execute-template --file \
  "$(chezmoi source-path)/.chezmoiscripts/run_once_before_00_install_prereqs.sh.tmpl" | sh
chezmoi apply
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
