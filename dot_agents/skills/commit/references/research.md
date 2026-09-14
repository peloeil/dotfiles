# 調査メモ：Conventional Commits と why-first なコミット

確認日：2026-09-14。対象：GPT-6 Astra を使うコーディングエージェント向けの commit skill。

## 結論

Conventional Commits は構造の基盤であって、変更理由の十分さを保証するものではない。本 skill は標準の形式を保ちつつ、完成メッセージの本文に具体的な why を必須にする。[S01][S02]

品質は「理由の欄があるか」ではなく、「変更前にどんな問題・制約・要求があり、この変更がなぜ必要かを説明できるか」で判定する。非自明な選択については解決方法の理由も必要だが、検討していない代案や確認できない効果を補ってはいけない。これは複数の指針をエージェント向けに統合した設計判断である。[S03][S04][S05]

調査内容をすべて実行時に読ませるのではなく、`SKILL.md` に必要な品質基準と操作範囲を残し、調査・例・評価素材を分離する。実行順序を固定した長いレシピにはしない。[S14][S15]

## 確認した 16 資料

各項目の「内容」は資料の要約、「反映」は今回の設計判断。プロジェクト固有の規約、著者の実践、研究結果を同じ強さの一般法則として扱わない。公開年だけで取捨選択せず、仕様の現行ページと古典的な一次記事を併読した。

### S01 — Conventional Commits 1.0.0

種別：公式仕様。内容：type、任意の scope、description、任意の本文・footer を規定し、破壊的変更の表示方法も定める。本文や why は必須ではない。反映：標準への準拠と、この skill 独自の「本文で why 必須」を区別する。

出典：`https://www.conventionalcommits.org/en/v1.0.0/`

### S02 — Angular: Commit Message Format

種別：プロジェクト公式規約。内容：本文で動機を説明し、必要に応じて変更前後の挙動を比較する。Angular 自身は docs を本文必須の例外とし、本文に最低文字数も設ける。反映：動機の明示は採用するが、固定文字数を意味の代わりにせず、今回の要望に合わせて docs も一文の理由を必須にする。

出典：`https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md`

本文確認：`https://raw.githubusercontent.com/angular/angular/main/contributing-docs/commit-message-guidelines.md`

### S03 — Git: SubmittingPatches

種別：Git プロジェクトへの貢献指針。内容：変更前の問題、解決後がよりよい理由、実際に検討して棄却した代案を説明する。反映：why を変更の必要性と解決方法の妥当性に分ける。Git プロジェクト固有の投稿手順は一般の commit skill に持ち込まない。

出典：`https://git-scm.com/docs/SubmittingPatches`

### S04 — Linux kernel: Submitting patches

種別：プロジェクト公式指針。内容：問題と利用者への影響、最適化の裏付け、トレードオフ、自己完結した説明、一つの問題に集中したパッチを重視する。反映：効果の捏造を避け、リンクだけで理由を済ませず、独立した意図を分割する。

出典：`https://www.kernel.org/doc/html/latest/process/submitting-patches.html`

### S05 — Google: Writing good CL descriptions

種別：公式エンジニアリング指針。内容：変更内容と理由、コードに現れない判断を将来の読者に伝える。外部リンクはアクセス制限や保存期限で読めなくなる可能性がある。反映：参照は補助とし、必要な背景をコミット内にも残す。CL の説明原則をコミット文案に応用するもので、Conventional Commits の仕様ではない。

出典：`https://google.github.io/eng-practices/review/developer/cl-descriptions.html`

### S06 — Chris Beams: How to Write a Git Commit Message

公開：2014-08-31。種別：著者の一次記事。内容：件名と本文の分離、短い件名、本文で変更内容と理由を伝えることを説く。軽微な変更では件名だけも認める。反映：コードの逐語訳を避ける原則を採用する一方、本文省略の例外は今回採用しない。

出典：`https://cbea.ms/git-commit/`

### S07 — Tim Pope: A Note About Git Commit Messages

公開：2008-04-19。種別：著者の一次記事。内容：短い件名と詳細説明を空行で分け、表示・利用するツールを意識した書式を示す。反映：構造の読みやすさを保つ。50/72 という慣行や大文字始まりを、すべての言語・リポジトリに一律適用するルールにはしない。

出典：`https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html`

### S08 — thoughtbot / Caleb Hearth: 5 Useful Tips For A Better Commit Message

公開：2013-04-26、更新：2015-06-12。種別：実務者の一次記事。内容：必要性、問題への対処、副作用を問い、変更が広がりすぎていないか見直す。反映：副作用を隠さず、コミットの意図が一つかを確認する。人間のエディタ操作に関する助言は、そのままエージェントのコマンド制約にはしない。

出典：`https://thoughtbot.com/blog/5-useful-tips-for-a-better-commit-message`

### S09 — thoughtbot / Valerie Burzynski: The art of writing meaningful Git commit messages

公開：2025-05-22。種別：実務者の一次記事。内容：Conventional Commits の機械可読性に加え、人が履歴を探しやすくなる意義を論じる。件名は単なる作業内容でなく、変更が達成する効果を伝えるべきだとする。反映：type 選びだけで満足せず、件名の意味も評価する。

出典：`https://thoughtbot.com/blog/the-art-of-writing-meaningful-git-commit-messages`

### S10 — thoughtbot / Rob Whittaker: Sixty-six commits and the commands that didn't survive

公開：2026-04-08。種別：Claude Code を使った著者自身の実践報告。内容：抽象的な why 重視の指示を、変更前・望む状態・実施内容という構成に改めた経験を記す。反映：抽象的な標語だけでなく、意味の合格条件を与える。ただし固定見出しが Astra でも優れるという実験結果ではないため、見出し自体は必須にしない。

出典：`https://thoughtbot.com/blog/sixty-six-commits-and-the-commands-that-didnt-survive`

### S11 — 後藤隼人：よい Git コミットメッセージを書くために気をつけるべきポイント

公開：2016-09-08。種別：著者の一次記事。内容：適度な具体性、文脈と理由、解決方法の選択理由、副作用、参照、スタイルの統一を整理する。反映：「注文処理を修正」のような曖昧さと、関数・行の説明だけの細かさの両方を避ける。

出典：`https://gotohayato.com/content/123/`

### S12 — Mitsuyuki.Shiiba：Gitのコミットメッセージは適当に書いてる

公開：2023-06-04。種別：著者のチーム実践についての一次記事。内容：小さな PR、事前の文脈共有、仕様書・コードコメントでの意図保存を前提に、個々のコミットを軽くする選択を説明する。反映：why を各コミットに残す運用が唯一の正解とは主張しない。今回はユーザーの要望からその運用を選び、冗長な重複は避ける。

出典：`https://bufferings.hatenablog.com/entry/2023/06/04/222124`

### S13 — Tian et al.: What Makes a Good Commit Message?

公開：2022-02-07。種別：研究論文の公開抄録を確認。内容：五つの活発な OSS の約 1,600 メッセージを対象に、平均で約 44% に改善の余地があると報告し、未選別データを用いる生成研究の課題を指摘する。反映：過去の履歴を無条件の品質見本にせず、意味と根拠を別に評価する。この割合はすべての Git 利用者の推定でも Astra の評価結果でもない。

出典：`https://arxiv.org/abs/2202.02974`

### S14 — OpenAI / Eric Provencher: Rethinking skills and prompts for GPT-6 Astra

公開：2026-09-11。種別：指定された公式記事。内容：短く適用範囲の明確な description、必要時に補助資料を読む構成、過剰な手順指定の削減、権限境界と完了点の見直しを勧める。反映：一般のコード編集では起動させず、コミット依頼時のローカル完了を明確にする。毎回の全資料通読・全テスト再実行・重複した許可確認を課さない。

出典：`https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra`

### S15 — OpenAI: Build skills

種別：公式ドキュメント。内容：`SKILL.md` の name と description、必要時の本文読込、ローカル配置場所を説明する。既定では命令文中心の skill を勧め、用途を絞り、起動条件もテストする。反映：単一用途の Markdown skill とし、通常運用に不要な評価素材を別ファイルにする。

出典：`https://developers.openai.com/codex/skills/`

確認時の転送先：`https://learn.chatgpt.com/docs/build-skills`

### S16 — Git: git-commit

種別：コマンド公式仕様。内容：通常のコミットは index を記録する。`-a` や pathspec を渡す場合は対象選択の意味が変わり、`--no-verify` は hook を迂回する。反映：作業ツリー全体ではなく実際の記録対象と文案を照合する。今回の安全方針として、無断の対象拡大・ステージ解除・hook 迂回を認めない。

出典：`https://git-scm.com/docs/git-commit`

## 意見が分かれる点と、今回の選択

**本文を常に書くか。** S01 は任意、S02 は docs に例外、S06 は自明な変更を例外にする。一方 S12 は、背景を別媒体に残すことを前提にコミットを軽量化する。今回の本文必須は、これらの資料全体の合意ではなく、ユーザーの「why を徹底する」という目的に合わせた選択である。

**how を書いてよいか。** 実装の逐語訳は避けるが、解決方法の選択理由を説明するための技術的な情報は有用である。how の全面禁止にはしない。[S03][S05][S08]

**固定テンプレートを強制するか。** S10 の実践からは具体的な構成を与える価値を読み取れるが、S14 を踏まえ、固定見出しより意味の必須条件を採用した。単純な誤記修正に複数の空欄を埋めさせない。

**履歴に従うか。** 言語や scope の慣習には合わせるが、既存の短すぎる本文や曖昧な理由は模倣しない。これは S13 の問題提起を踏まえた設計判断である。

## エージェント向けに追加した方針

理由の捏造禁止、メッセージ作成と実コミットの権限分離、無関係な staged 変更の保護、成功報告と実記録の照合は、資料を基に今回追加した運用上の制約である。Conventional Commits の要件でも、特定モデルについて実証された性能保証でもない。

構文検査で本文の有無や形式を確認できても、理由の真偽・十分さはそれだけでは確定しない。`evals/cases.md` では、形式、意味、根拠、変更範囲、実行権限、完了状態を別々に評価する。

## 調査・検証の限界

この調査は目的に沿った一次資料の比較であり、全記事を網羅した体系的レビューではない。S13 は公開抄録の範囲のみを使用した。リンク先の本文を再取得できなかった記事は 16 資料に数えていない。

本パッケージについて確認したのはファイル構造・frontmatter・参照整合性などの静的な項目であり、Astra による実リポジトリ上の性能評価ではない。評価ケースは未実施の受け入れ試験素材である。
