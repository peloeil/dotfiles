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

- 依頼者・`AGENTS.md`・`CONTRIBUTING.md`・commitlint などの規約を優先する。規約がなければこの skill を使い、履歴は scope 名の確認だけに使う。
- `git diff` に出ない未追跡ファイルも確認する。タスク文書・秘密情報・依頼範囲外は除外し、生成物は成果物か判断する。
- staged 変更を外さない。同じファイル内で今回の対象と混在していれば確認し、分離できるファイルだけ `git commit --only -- <paths>` を使う。

## 2. コミットを分ける

- 1 コミット = 1つの独立して戻せる目的。同じ目的の実装・テスト・文書はまとめる。
- 独立して戻せる変更だけを分け、安全に分割できない hunk は無理に切り離さない。

## 3. 作業過程から切り離してメッセージを作る

コミットメッセージの初稿は、可能なら新しい Codex agent に委譲する。親セッションの会話を渡さず、`rtk codex exec --model gpt-5.6-luna --config 'model_reasoning_effort="max"' --ephemeral -C <repo> --sandbox read-only` で起動する。

agent には現在の `git status --short -uall`、`git diff`、`git diff --cached`、未追跡ファイルの内容、適用される規約だけを読ませ、差分に基づく Conventional Commit message を 1 案出させる。編集、stage、commit、commit skill の再起動、さらなる agent の起動はさせない。ユーザーの依頼文、作業中の説明、親 agent の推測、候補メッセージは渡さない。親 agent は候補を実差分に照合してから採用する。

read-only sandbox の起動失敗（`bwrap` や loopback など）の場合に限り、同じ ephemeral agent を `rtk codex --ask-for-approval never exec --model gpt-5.6-luna --config 'model_reasoning_effort="max"' --ephemeral -C <repo> --dangerously-bypass-approvals-and-sandbox` で再試行できる。この経路はローカル差分の確認だけに使い、agent の prompt に編集・stage・commit・外部アクセスを禁止すると明記する。sandbox 以外の失敗、またはこの再試行が失敗した場合は raw diff だけを再読して自分で初稿を作る。

## 4. メッセージを書く

Conventional Commits の subject に変更内容、body に変更前の問題と必要性を書く。全 type に body を付ける。

- 規約がなければ英語・命令形・小文字始まり・末尾ピリオドなし。scope は対象が明確な場合だけ付ける。
- 根拠は差分・確認した規約・事実に限り、diff の言い換えと推測を避ける。

## 5. stage してコミットする

- `git add -A`/`.` は使わず対象パスを明示する。部分変更は `git add -p` で分ける。
- stage 後に `git diff --cached` で内容・秘密情報・分割単位を確認し、関連する既存チェックを走らせる。
- メッセージは `git commit -F -` に渡す。

各コミット後に `git show --stat --oneline HEAD` と `git status --short -uall` を確認する。

## 6. 間違えたコミットを直す

共有済みのコミットは書き換えず追加コミットで直す。未共有と確認できた場合だけ amend/rebase を使う。

- 直前のメッセージは `git commit --amend`、入れ忘れは対象を stage して cached diff を確認後に amend する。
- amend 前は必ず `git diff --cached` を確認する。`git stash`、`git reset --hard`、`git checkout --`、`git restore` は使わない。
