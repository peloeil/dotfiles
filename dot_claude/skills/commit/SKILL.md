---
name: commit
description: Inspect working-tree changes, split them into small reversible Conventional Commits, and write messages whose bodies explain the problem and reason for the change. Use when asked to commit changes, split changes into commits, write or fix commit messages, or follow a repository's explicit commit policy.
---

# commit

依頼された変更だけを、安全に戻せる単位でコミットする。コミットを頼まれていないなら実行しない。

## 1. 全差分と明文化された規約を確認する

最初に次を確認する。

```sh
git status --short -uall
git diff
git diff --cached
```

- 規約は、依頼者の指示、`AGENTS.md`、`CONTRIBUTING.md`、commitlint などの設定を優先する。
- 明文化された規約がなければ、この skill の規則をそのまま使う。履歴から規約を推測しない。
- 履歴は、明文化された規約と矛盾しない既存の scope 名を探すときだけ必要な範囲で見る。
  過去の誤った type、本文の欠落、曖昧な subject、ばらついた書式を引き継がない。
- 未追跡ファイルは `git diff` に出ない。必要なら
  `git diff --no-index -- /dev/null <path>` で中身まで読む。
- 作業用のタスク文書 (`docs/tasks/**` の類)、秘密情報、依頼範囲外の変更は除外する。
- 生成物は一律に除外しない。リポジトリに残すべき成果物かを差分ごとに判断する。
- 既に stage された変更もユーザーの作業として扱い、勝手に外さない。今回のコミットに含めない
  stage 済み変更があるなら、対象がファイル単位で分かれている場合だけ `git commit --only -- <paths>` を使う。
  同じファイル内で混在しているなら、勝手に index を組み替えず依頼者に確認する。

## 2. コミットを分ける

- **1 コミット = 戻しやすい 1 目的。**
- 目的が同じなら、実装・テスト・仕様書の更新をまとめる。ひとつの文書更新も分割しない。
- 別々に戻す可能性がある目的だけを分ける。
- 同じ目的の差分は、誰が書いたかではなく内容でまとめる。
- hunk を安全に分けられない変更は、無理に別コミットへ切り離さない。

## 3. メッセージを書く

Conventional Commits の subject に変更内容、本文に「変更前の問題」と「この変更が必要な理由」を書く。
本文は `feat` や `docs` を含むすべてのコミットに付ける。

- 明文化された規約がなければ、subject と本文は英語、scope は対象が明確なときだけ、subject は
  命令形・小文字始まり・末尾ピリオドなしを既定とする。
- 本文だけを読んで、なぜ変更が必要だったか分かるようにする。
- diff の言い換えは書かない。壊れ方、再現条件、危険、読みにくさなど、変更前の状態を具体的に書く。
- 根拠は作業中に確認した事実、コード、設計文書、issue、過去の変更理由に限る。履歴は Why の
  根拠には使ってよいが、メッセージの書式や品質は真似しない。推測で Why を補わない。
- scope は対象を特定できるときだけ付ける。複数箇所なら `fix(bash,fish)` のように併記してよい。
- 履歴に適切な type がなくても、変更の性質を偽らない。

## 4. stage してコミットする

- `git add -A` と `git add .` は使わず、対象パスを明示する。
- ファイル内の一部だけなら `git add -p` を使う。hunk は `s`、必要なら `e` で分ける。
  非対話環境では応答を stdin に渡す。stdin が `/dev/null` だと何も stage せず成功することがある。
- コミット前に `git diff --cached` で、内容・秘密情報・分割単位を再確認する。
- 実行可能な既存のチェックを走らせる。
- 本文の改行と shell の展開を避けるため、メッセージは `-F` で渡す。

```sh
git commit -F - <<'MSG'
<type>(<scope>): <subject>

<変更前の問題と、この変更が必要な理由>
MSG
```

各コミット後に `git show --stat --oneline HEAD` と `git status --short -uall` を確認する。

## 5. 間違えたコミットを直す

共有済みのコミットは書き換えず、追加コミットで直す。`git log --oneline @{u}..HEAD` は upstream に
含まれないコミットを確認する手掛かりにすぎない。upstream がなくても未 push とは限らないため、
共有されていないと確認できない履歴は書き換えない。

未共有と確認できた場合だけ、次を使う。

| 直すもの | 操作 |
| --- | --- |
| 直前のメッセージ | `git commit --amend` |
| 直前の入れ忘れ | `git add -- <path>` → `git diff --cached` → `git commit --amend --no-edit` |
| 直前への混入 | `git restore --source=HEAD^ --staged -- <path>` → `git diff --cached` → `git commit --amend --no-edit` |
| 過去のメッセージや分割 | `git rebase -i` |

`git commit --amend` は stage 済みの変更をすべて取り込む。必ず直前に `git diff --cached` を見る。
複数コミットを分け直すなら、未共有を確認してから `git reset <分岐点>` で作業ツリーへ戻す。
`--soft` は使わない。

`git stash`、`git reset --hard`、`git checkout -- <path>`、`git restore <path>` は使わない。
ユーザーの変更を失う可能性がある。
