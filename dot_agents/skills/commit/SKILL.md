---
name: commit
description: Create focused Conventional Commits or revise commit messages when requested.
---

# commit

依頼された変更を、独立して戻せる目的ごとにコミットする。同じ目的の実装・テスト・文書はまとめ、分割できない変更を無理に切り離さない。メッセージ作成だけの依頼ではコミットしない。

## メッセージの規約

依頼者とリポジトリの明文化された規約を優先する。規約がなければ次を使う。

- Conventional Commits。subject は英語・命令形・小文字始まり・末尾ピリオドなし。scope は対象が明確な場合だけ付ける。
- 全 type に body を付け、変更前の問題と変更の必要性を書く。
- 最終的な差分と確認した事実を根拠にする。作業の経緯や差分の言い換えで埋めず、不明な動機を推測しない。

## 変更を守る

`git status --short -uall`、`git diff`、`git diff --cached` と未追跡ファイルから対象を判断する。秘密情報・依頼範囲外の変更を含めない。

既存の staged 変更を外したり、作業ツリーを退避・破棄したりしない。対象パスや hunk を指定して stage する。別ファイルの staged 変更を残すには `git commit --only -- <paths>` を使えるが、同じファイル内で対象を安全に分離できない場合は確認する。

コミットする差分と必要な検証結果を確認し、メッセージは `git commit -F -` に渡す。コミット後は作成内容と残った変更を確認する。

履歴の修正を依頼された場合、未共有と確認できたコミットだけ amend/rebase する。共有済みなら追加コミットで直す。amend でも既存の staged 変更を混入させない。
