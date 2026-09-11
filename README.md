# dotfiles

新しいマシンに普段の開発環境を復元するための dotfiles。
主な対象は Linux デスクトップで、Codex CLI 以外のツールとランタイムは `mise` で管理する。
Codex CLI は remote control に必要な standalone installer で管理する。

## 新しいマシンをセットアップする

Gentoo では、事前に `app-i18n/mozc` の `fcitx5` USE フラグを有効にする。

暗号化ファイルを復号するため、先に age の秘密鍵を配置する。

```sh
mkdir -p ~/.config/chezmoi
# USB やパスワードマネージャーから秘密鍵をコピーする
cp /path/to/key.txt ~/.config/chezmoi/key.txt
chmod 600 ~/.config/chezmoi/key.txt
```

chezmoi をインストールし、このリポジトリを適用する。

```sh
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply peloeil
```

途中で Git の名前、メールアドレス、研究用メールアドレス、研究用ディレクトリを入力する。
dotfiles、Linux の前提パッケージ、`mise` と開発ツール、fish tools、フォント、Neovim の plugin、AI ツールの plugin が順にセットアップされる。

sudo 権限がない場合は前提パッケージの導入だけがスキップされる。不足分は別途インストールする。

## 研究用メールの自動切り替え

研究用メールは [Git の条件付き include](https://git-scm.com/docs/git-config#_conditional_includes) で自動選択する。対象の既定値は `~/workspace/univ/lab/research/`。場所を変える場合は `chezmoi edit-config` で `[data]` の `researchDir` を絶対パスまたは `~/...` に設定し、`chezmoi apply` する。`researchDir` が未設定の既存環境でも既定の場所を使う。

リポジトリで実際に使われるメールは次で確認できる。個別の `git config --local user.email` があれば、そちらが優先される。

```sh
git config --show-origin --get user.email
```

## 普段使うコマンド

```sh
# 管理対象を編集する（target path を指定）
chezmoi edit ~/.config/fish/config.fish

# 差分を確認して反映する
chezmoi diff
chezmoi apply

# リポジトリの更新を取得して反映する
chezmoi update

# 状態を確認する
chezmoi doctor
mise doctor

# Codex CLI を更新する
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```
