# dotfiles

新しいマシンで普段の環境を復元するための `chezmoi` 管理リポジトリ。
ツール管理は `mise`、主な対象は Linux デスクトップ。

## セットアップ

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply peloeil
```

初回 `apply` では次を聞かれる。

- Git の `email`
- Git の `name`
- `machine_type` (`desktop` か `server`)

これで次が適用される。

- dotfiles
- Git / shell などの設定
- `mise` 本体
- `~/.config/mise/config.toml` に書いたツール
- Linux では前提パッケージ導入スクリプト

デスクトップ周りの設定は Linux 前提。内部実装のメモは `AGENTS.md` に置いてある。

## 普段やること

```bash
# dotfiles を編集
chezmoi edit <path>

# 反映前に差分を見る
chezmoi diff

# 反映する
chezmoi apply

# repo を更新して反映
chezmoi update

# 状態確認
chezmoi doctor
mise doctor
```
