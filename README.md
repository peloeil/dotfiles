# dotfiles

このリポジトリは、自分の開発環境を宣言的に再現するための単一ソース。
目的は「新しいマシンを用意したときに、設定のドリフトなしで同じ環境を即復元すること」。

設計の中核は chezmoi（設定管理） と mise（ツール・ランタイム管理）。

## 設計思想

### 1. すべてをコードで定義
- dotfiles・設定値・ツールバージョン・OSごとの差分をすべて Git 管理。
- 手動変更はドリフトの原因になるため、基本的に編集は `chezmoi edit` 経由。

### 2. マシン固有値はテンプレートに閉じ込める
- `.tmpl` によってユーザ名・メールアドレス・OS 判定などを管理。
- マシンによって差異が出る部分はテンプレート条件分岐で吸収する。

### 3. 必要なものはすべて宣言する
- mise の `config.toml` に言語ランタイム／CLI／補助ツールを列挙。
- run\_onchange スクリプトで、宣言に変化があったときだけ適用。

### 4. セットアップは 1 コマンド
新しいマシンでやることはこれだけ：
```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply peloeil
````

これにより：

* chezmoi 自体のインストール
* dotfiles の clone
* テンプレート展開
* shell 設定、git 設定、その他 dotfiles の適用
* mise の有効化（シェルフック／ツールインストール）
  が自動で終わる。

## 運用フロー（自分のための手順メモ）

### 設定を変更したいとき

```bash
chezmoi edit --apply ~/.zshrc
```

もしくは対象ファイルを直接指定。
`.tmpl` を編集するときはテンプレート値の反映も含めて `apply` に任せる。

### ツールを追加したいとき（mise）

```bash
chezmoi edit ~/.config/mise/config.toml
chezmoi apply -v
```

次回のシェル起動時に mise が必要ツールを自動インストール。

### 他マシンに追従したいとき

```bash
chezmoi update
```

### 適用前に差分を確認したい

```bash
chezmoi diff
```

### トラブルシュート

```bash
chezmoi doctor
mise doctor
```

## ディレクトリ構造（自分が迷わないための最小メモ）

* `.chezmoi.toml.tmpl`
  → chezmoi の基本設定とマシン固有値のテンプレート。

* `.chezmoiscripts/`

  * `run_once_…`：最初の apply のときに一度だけ走る。
  * `run_onchange_…`：対応するファイル・データに変更があったときのみ実行。
    設定の再適用やパッケージの更新をここで制御する。

* `dot_config/mise/config.toml`
  → mise のツール一覧。
  バージョン固定 or latest をここで宣言。

## このリポジトリで再現されるもの（要点だけ）

* git 設定（ユーザ情報はテンプレート）
* mise のツールセット（言語ランタイムと CLI 群の固定化）
* システムパッケージの自動導入
* 各種 dotfiles

これらはすべて chezmoi apply の一回で揃う。

## 依存ツールと用途（どこで必要になるか）

### 管理・導入まわり
* chezmoi：このリポジトリの適用自体に必要。
* mise：ツール管理。`dot_config/mise/config.toml` と `.chezmoiscripts/run_onchange_after_10_install_mise_tools.sh.tmpl`。
* curl / sudo / apt-get / pacman / emerge：前提インストール。`.chezmoiscripts/run_once_before_00_install_prereqs.sh.tmpl`。
* curl：mise インストールや fish/fisher の導入で使用。`.chezmoiscripts/run_once_before_01-install-mise.sh.tmpl` / `.chezmoiscripts/run_once_00-install-fish-tools.fish`。

### エディタ・開発ツール（主に mise 管理）
* neovim：Neovim 設定の本体。`dot_config/nvim/init.lua`。
* deno：denops/dpp の設定実行に必要。`dot_config/nvim/config.ts`。
* ripgrep / fd / fzf：ddu ソースで使用。`dot_config/nvim/toml/ddu.toml`。
* lua-language-server / pyright / clangd / zls / stylua / ruff：LSP/formatter 周り。`dot_config/nvim/hooks/lsp.lua` / `dot_config/nvim/toml/no_lazy.toml` / `dot_config/nvim/hooks/conform.lua`。
* uv：python を uv 経由で導入。`.chezmoiscripts/run_onchange_after_10_install_mise_tools.sh.tmpl`。

### Git 周り
* git：リポジトリ管理および Git 設定の適用に必須。
* delta：git の pager/diff に使用。`dot_config/git/private_config.tmpl`。

### シェル・ターミナル
* fish：デフォルトシェル。`dot_config/tmux/tmux.conf` / `dot_config/private_fish/config.fish`。
* fisher：fish プラグイン管理。`.chezmoiscripts/run_once_00-install-fish-tools.fish`。
* tmux：ターミナルマルチプレクサ。`dot_config/tmux/tmux.conf`。

### デスクトップ/WM
* i3：WM 本体とキー設定。`dot_config/i3/config.tmpl`。
* alacritty：ターミナル。`dot_config/alacritty/alacritty.toml.tmpl` / `dot_config/i3/config.tmpl`。
* polybar：バー表示。`dot_config/polybar/config.ini` / `dot_config/i3/executable_polybar.sh`。
* picom：コンポジタ。`dot_config/picom/picom.conf` / `dot_xprofile.tmpl`。
* rofi / feh / nm-applet / blueman-applet / xss-lock / i3lock / pactl / xbacklight / flameshot：起動コマンド・キー割当。`dot_config/i3/config.tmpl`。
* killall / pgrep：polybar 起動スクリプトで使用。`dot_config/i3/executable_polybar.sh`。
* Xorg（Xorg サーバ、xinit/startx）：i3 を動かすための基盤（display manager がない環境向け）。

### 入力・クリップボード
* fcitx5 / mozc：日本語入力。`dot_xprofile.tmpl` / `dot_config/private_fcitx5/private_profile`。
* xclip：tmux のコピー。`dot_config/tmux/tmux.conf`。

### フォント
* Hack Nerd Font：Alacritty/Polybar のフォント。`dot_config/alacritty/alacritty.toml.tmpl` / `dot_config/polybar/config.ini`。
* curl / wget / unzip / bsdtar / python3 / fc-cache：フォント導入スクリプトで使用。`.chezmoiscripts/run_onchange_after_20_install_hack_nerd_font.sh`。

## 追加メモ

* 機密情報は `.tmpl + 変数` で扱い、平文で保持しない。
* 実行順序が必要なものは run_once / run_onchange を使う。

## 最低限覚えておくコマンド一覧

```bash
# 新規マシンセットアップ
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply peloeil

# 普段の更新
chezmoi edit <path>
chezmoi apply

# 差分
chezmoi diff

# pull + apply
chezmoi update
```
