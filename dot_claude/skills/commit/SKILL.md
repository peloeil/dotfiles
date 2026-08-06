---
name: commit
description: Split working-tree changes into Conventional Commits — each one simple and small, each message body stating the problem and why this change. Also covers which changes to leave out, how to match a repository's existing style, and how to fix a commit that came out wrong. Use when asked to commit changes, split changes into commits, write or fix commit messages, or match a repository's commit style.
---

# commit

**コミットする前に `git log -40` を読む。** type と scope の語彙、subject の語形を、そこに合わせる。

## 分ける

- **1 コミット = 戻しやすい 1 単位。**
- **割りすぎない。** 目的がひとつなら、実装・テスト・仕様の調整は 1 コミット。
  ひとつの文書更新を複数に割らない。実装と恒久文書のように、**目的が違うものだけ**分ける。
- **同じ論理変更に属する差分は、自分が書いたものでなくても含める。**
- **範囲の外に出ない。** 作業用のタスク文書 (`docs/tasks/**` の類) と秘密情報は入れない。
  生成物は毎回判断する。生成スクリプトを消して lockfile を履歴に残す、のように
  **生成結果そのものを残したい場合がある。**

## 書く

- **subject は変更内容の要約。本文には「何が問題で、なぜこの変更か」を書く。**
  **本文はすべてのコミットに書く。`feat` も `docs` も。**
  履歴のコミットに本文が無くても書く。履歴に合わせるのは type と scope の語彙、subject の語形まで。
- **本文が diff の言い換えなら、それは本文ではない。**
  判定は、**その本文だけを読んで「なぜ要ったか」が分かるか**。
  変更前に何が起きていたか (壊れ方、再現条件、危険、読みにくさ) を具体的に書く。
- **Why の根拠が無いなら書かない。** 根拠は、今の作業で知っていること、コード、`git log`、
  設計文書や issue。どこにも無ければ、diff から読める「何が問題だったか」で止める。**推測で埋めない。**
- **規約適合より、後から見返したときの分かりやすさ。** scope は「これを見て対象が分かるか」で選ぶ。
  複数箇所に跨るなら `fix(bash,fish)` でよい。履歴の語彙に、その変更を正しく表す type が
  無いなら標準の type を使う。**変更の性質を偽ってまで履歴に寄せない。**

## やらない

- **規約を発明しない。** ブランチを切る・PR にする・push する・squash する —
  **指示があるか、そのリポジトリの履歴と設定に根拠があるときだけ。**
  「一般にそうすべき」で足さない。**main へ直接コミットしてよい。**
- **コミットしろと言われたときだけコミットする。**
- 行長、末尾ピリオド、scope の必須性、メッセージの言語、trailer、署名、merge 方針 —
  **決まりは無い。** 履歴に合わせ、履歴にも無ければ聞く。

## 黙って壊れるところ

- **`git status --short` は未追跡ディレクトリを `?? docs/` と畳む。** `git diff HEAD` にも
  未追跡ファイルの中身は出ない。**`-uall` を付ける。** 付けないと、上で「入れるな」と書いた
  タスク文書と `.env` が見えないまま通る。中身は `git diff --no-index -- /dev/null <path>`。
- **`git add -A` と `git add .` を使わない。** 範囲外を巻き込む。stage は明示的に。
- **`git add -p` は stdin が `/dev/null` だと、終了コード 0 のまま何も stage しない。**
  応答を流せば非対話でも動く (`printf 'n\ny\n' | ...`)。
  1 つの hunk に別々の関心事が入っているなら `s` で割る。割れないなら `e`。
  それも無理なら**その 2 つは 1 コミットにする**。
- **`-m` は本文の改行を保てない。** 本文があるなら:

  ```sh
  git commit -F - <<'MSG'
  <subject>

  <本文>
  MSG
  ```
- **`git commit --amend` はその時点で stage されている全部を取り込む。**
  無関係な変更が直前のコミットに吸い込まれ、作業ツリーの変更一覧から消える。
  **amend の前に `git diff --cached` を見る。**
- **`git stash` / `git reset --hard` / `git checkout -- <path>` / `git restore <path>` を使わない。**
  変更が消える。

## 直す

`git log --oneline @{u}..HEAD` に出るものが未 push。upstream が無ければ (`fatal: no upstream`)
どこにも出していない。**push 済みなら履歴を書き換えず、追加のコミットで直す。**

| 直すもの | 未 push なら |
| --- | --- |
| 直前のメッセージ | `git commit --amend` |
| 直前の入れ忘れ | `git add -- <path>` → `git commit --amend --no-edit` |
| 直前への混入 | `git restore --source=HEAD^ --staged -- <path>` → `git commit --amend --no-edit` |
| 過去のメッセージ、分割のやり直し | `git rebase -i` (対話的なので自分でやる) |

**コミット後の `git restore --staged` は何もしない** (index は既に HEAD と同じ)。`--source=HEAD^` が要る。

やり直しが 2 コミット以上に及ぶなら `git reset <分岐点>` で戻してやり直す。
**`--soft` を付けると全変更が stage 済みで戻る**ので、分け直すなら付けない。
**`--hard` は使わない。**
