# dotfiles

新しいマシンに普段の開発環境を復元するための dotfiles。
主な対象は Linux デスクトップで、ツールとランタイムは `mise` で管理する。

## 新しいマシンをセットアップする

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

途中で Git の名前、メールアドレス、研究用メールアドレスを入力する。
dotfiles、Linux の前提パッケージ、`mise` と開発ツール、フォント、fish tools、AI ツールの plugin が順にセットアップされる。

sudo 権限がない場合は前提パッケージの導入だけがスキップされる。不足分は別途インストールする。

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
```
