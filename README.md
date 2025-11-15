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
