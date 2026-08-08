---
name: writeup
description: Write or revise an evidence-backed explanation of a codebase, subsystem, experiment, or result for someone who will not read the code. Use for onboarding documents, design explanations, reports, postmortems, handoff notes, README rewrites, and prose reviews. Claude controls the workflow while separate fresh-context Codex sessions investigate, write, fact-check, and judge the document as a reader.
---

# writeup

Claude は統制役、Codex は実働役とする。Claude は対象と合格条件を決め、Codex の報告を裁定する。
調査、執筆、事実検証、読者評価は Claude 自身や Claude のサブエージェントで代行しない。

各 Codex は `codex exec --ephemeral` で新規起動し、前工程の会話、報告、Claude の見立てを渡さない。
ここでいう fresh-context は前工程の内容を継承しないという意味で、Codex 共通の system instructions まで
消えるという意味ではない。`codex` が使えなければ Claude だけで続けず、依頼者へ伝える。
Codex ごとに空の専用ディレクトリを作り、その工程で許可する brief だけをコピーする。

## 1. 合格条件を固定する

依頼と対象から次を決める。読み手と読後の目的が不明なら、そこだけは依頼者に聞く。

- 読み手と、その人が知っている用語
- 読後にできるべき判断または作業
- 文書が答える中心的な問い
- 扱う範囲と扱わない範囲
- 対象文書と、コード、実行結果、一次資料の絶対パス
- 実行してよい確認コマンドと、その作業ディレクトリ。なければ「なし」

問い、実行経路、責任範囲のいずれかが途中で変わるなら文書を分ける。

主張と根拠を混ぜない。

| 主張 | 根拠 |
| --- | --- |
| 実装、構造、依存、条件 | 現在のコードと設定 |
| 挙動、数値、性能 | 実行結果、ログ、テスト出力 |
| 目的、経緯、設計意図 | 当時の設計文書、issue、PR、コミットメッセージ |
| 本番の状態、運用上の契約 | 実環境の記録 |

README、wiki、過去の説明、コード内コメントは調査の入口であり、実装上の事実の根拠ではない。
中心的な問いへの答えを対応する根拠から確認できない場合は、作業前に不足を依頼者へ伝える。

## 2. Codex に渡す brief を作る

対象リポジトリの外に空の作業領域を作る。Claude Code の Bash は呼び出しごとに変数が消えるので、
必要な変数は各コード断片の先頭で定義し直す。

```sh
W="<一時作業領域>/writeup-<一意な名前>"
S="$HOME/.claude/skills/writeup/prompts"
command -v codex >/dev/null || { echo "codex CLI が要る"; exit 1; }
for f in writer factcheck reader; do
  test -r "$S/$f.md" || { echo "$S/$f.md がない"; exit 1; }
done
test ! -e "$W" || { echo "$W は使用済み。別の名前にする"; exit 1; }
mkdir -p "$W" || exit 1
```

Claude は `$W/control.md` に次だけを書く。

- 対象文書の絶対パス。新規か既存か
- 読み手、既知の用語、読後の目的、中心的な問い、対象内、対象外
- コード、実行結果、一次資料、根拠にしない資料の絶対パス
- 実行を許可したコマンド、作業ディレクトリ、出力先。許可しないなら「なし」
- 出力言語と形式

別に `$W/reader.md` を作り、読み手、既知の用語、読後の目的、中心的な問い、対象内、対象外、対象文書の
絶対パスだけを書く。コード、根拠、調査経緯、Claude の評価は入れない。

実行を許可するのは、所要時間と影響範囲を見積もれ、外部送信、課金、秘密の読み出し、既存成果物の
上書き、永続的な状態変更を伴わないコマンドだけとする。判断できなければ依頼者に聞く。

## 3. 原稿を用意する

既存文書は作業領域へコピーする。新規文書は fresh-context の Writer に作業領域内で書かせる。
対象文書の置き場所にはまだ書き込まない。

```sh
W="<手順 2 で決めた作業領域>"
S="$HOME/.claude/skills/writeup/prompts"
D="<対象文書の絶対パス>"
if test -e "$D"; then
  cp "$D" "$W/document.md" || exit 1
else
  mkdir "$W/write-1" || exit 1
  cp "$W/control.md" "$W/write-1/control.md" || exit 1
  set -o pipefail
  { cat "$S/writer.md"; printf '\nCONTROL_BRIEF: %s\nDOCUMENT: %s\n' \
      "$W/write-1/control.md" "$W/write-1/document.md"; } \
    | codex exec --ephemeral -C "$W/write-1" --sandbox workspace-write \
        --skip-git-repo-check -o "$W/write-1/report.md" - \
    && test -s "$W/write-1/report.md" && test -s "$W/write-1/document.md" \
    || { echo "Writer が失敗、または空"; exit 1; }
  cp "$W/write-1/document.md" "$W/document.md" || exit 1
fi
```

新規文書では、Claude は `write-1/report.md` に中心的な問いを妨げる未確認事項がないことだけを確認する。
文章の良し悪しや事実は次の Codex に判定させる。

## 4. 独立評価する

Fact-checker と Reader を毎回新規に、並行して起動する。`N` は評価回数で、最初は `1` とする。

```sh
W="<手順 2 で決めた作業領域>"
S="$HOME/.claude/skills/writeup/prompts"
N=1
set -o pipefail
mkdir "$W/fact-$N" "$W/read-$N" || exit 1
cp "$W/control.md" "$W/fact-$N/control.md" || exit 1
cp "$W/reader.md" "$W/read-$N/brief.md" || exit 1
{ cat "$S/factcheck.md"; printf '\nCONTROL_BRIEF: %s\nDOCUMENT: %s\n' \
    "$W/fact-$N/control.md" "$W/document.md"; } \
  | codex exec --ephemeral -C "$W/fact-$N" --sandbox workspace-write \
      --skip-git-repo-check -o "$W/fact-$N/report.md" - &
pf=$!
{ cat "$S/reader.md"; printf '\nREADER_BRIEF: %s\nDOCUMENT: %s\n' \
    "$W/read-$N/brief.md" "$W/document.md"; } \
  | codex exec --ephemeral -C "$W/read-$N" --sandbox read-only \
      --skip-git-repo-check -o "$W/read-$N/report.md" - &
pr=$!
ng=0
for p in "$pf" "$pr"; do wait "$p" || ng=1; done
test "$ng" = 0 && test -s "$W/fact-$N/report.md" && test -s "$W/read-$N/report.md" \
  || { echo "評価が失敗、または空"; exit 1; }
```

Fact-checker には原稿と生の根拠だけ、Reader には原稿と読者条件だけが渡る。この分離を崩さない。

## 5. Claude が裁定し、Codex が直す

Claude は二つの報告を読み、`$W/decisions.md` に次だけを書く。

- 必ず直す事実誤認と誤解を招く記述
- 削る、または「未確認」と明記する裏の取れない主張
- 想定読者が実際に困る理解上の問題
- 削る不要な文と、必要な構成変更
- 依頼者の要求でまだ原稿に入っていない内容

指摘を転載せず、採否を決めた変更だけを書く。報告が食い違う場合、Claude が推測で決めず、争点だけを
書いた質問を fresh-context の Fact-checker に渡して、生の根拠から再判定させる。

新しい Writer に `control.md` と `decisions.md` だけを渡して直させる。評価報告は渡さない。

```sh
W="<手順 2 で決めた作業領域>"
S="$HOME/.claude/skills/writeup/prompts"
R=2
set -o pipefail
mkdir "$W/write-$R" || exit 1
cp "$W/control.md" "$W/decisions.md" "$W/document.md" "$W/write-$R/" || exit 1
{ cat "$S/writer.md"; printf '\nCONTROL_BRIEF: %s\nDECISIONS: %s\nDOCUMENT: %s\n' \
    "$W/write-$R/control.md" "$W/write-$R/decisions.md" "$W/write-$R/document.md"; } \
  | codex exec --ephemeral -C "$W/write-$R" --sandbox workspace-write \
      --skip-git-repo-check -o "$W/write-$R/report.md" - \
  && test -s "$W/write-$R/report.md" && test -s "$W/write-$R/document.md" \
  || { echo "Writer が失敗、または空"; exit 1; }
cp "$W/write-$R/document.md" "$W/document.md" || exit 1
```

## 6. 修正版を再評価する

工程 4 を `N=2` として、別の Fact-checker と Reader で再実行する。合格条件は次のとおり。

- 事実の誤りがない
- 結論に必要な主張に「裏が取れない」がない
- 読者が文書だけで中心的な問いに答え、目的の判断または作業をできる
- 内部矛盾がなく、削っても読者の理解や行動が変わらない文がない

不合格なら工程 5 と 6 を新しい Codex で繰り返す。根拠不足で直せない、または同じ争点が残る場合は
無理に合格させず、未解決事項として依頼者へ返す。繰り返すたびに `R` と `N` を増やし、既存の
専用ディレクトリを再利用しない。

合格後に Claude が `$W/document.md` と対象文書の差分を確認し、対象文書の絶対パスへこの1ファイルだけを
コピーする。読者向け本文は結論と次の行動で終える。ドキュメントとコードの不一致、確認できなかったこと、
採用しなかった事実関係の指摘は本文に混ぜず、依頼者への報告または別のメモに残す。
