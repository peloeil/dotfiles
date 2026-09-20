# Codex の Discord 完了通知

既定では 600 秒以上かかった回答の完了時に、指定ユーザーをメンションして通知する。
所要時間にはコマンド実行や承認待ちも含む。しきい値に達した時点では投稿しない。

Python 3.11 以上と、`UserPromptSubmit` / `Interrupt` / `notify` に対応した
Codex CLI が必要。追加の Python パッケージは不要。

## 設定する

chezmoi でコードと `config.example.json` を配置した後、各マシンで設定する。
Bot には対象チャンネルの閲覧・送信権限が必要。

初回は設定例をコピーして編集する。既存の `config.json` がある場合はコピーせず、
そのファイルを編集する。

```sh
install -m600 "$HOME/.codex/discord-notify/config.example.json" "$HOME/.codex/discord-notify/config.json"
$EDITOR "$HOME/.codex/discord-notify/config.json"
```

`config.json` に次を設定する。

- `bot_token`: 投稿する Bot のトークン。
- `channel_id`: 投稿先チャンネル ID。
- `mention_user_id`: メンションするユーザー ID。
- `threshold_seconds`: 通知のしきい値。初期値は 600 秒。

Bot トークンを含む `config.json` は暗号化しても chezmoi の管理対象に加えない。
`.chezmoiignore` でこの設定・実行状態・キャッシュを除外している。
トークンは各マシンで設定するか、既存の設定ファイルを別途安全に転送する。

設定後、インストーラーで Codex に登録する。

```sh
python3 "$HOME/.codex/discord-notify/install.py"
```

登録後は Codex を再起動し、`/hooks` でこのディレクトリの `notify.py` を
呼ぶ `UserPromptSubmit` と `Interrupt` をレビューして信頼済みにする。
Codex は新しいフックを信頼済みにするまで実行しない。

## 登録と更新

インストーラーは `$CODEX_HOME`（既定は `~/.codex`）の `config.toml` と
`hooks.json` に登録する。通知ディレクトリの権限は 700、`config.json` は 600 に設定する。
既存の設定を保ち、再実行しても同じフックを重複登録しない。
別の `notify` コマンドやインラインのフック定義がある場合は上書きせず停止する。
変更前のファイルは初回だけ `*.before-discord-notify` に保存する。

chezmoi の after script は `run_onchange` で、初回または前回成功時から
スクリプトの展開内容が変わったときに実行される。`notify.py` と `install.py` の
ハッシュを含むため、これらのコード更新時も再登録する。
`~/.local/bin/codex` が実行できないか、ローカルの `config.json` がなければスキップする。
スキップ後に不足分を用意した場合は、上の `install.py` を直接実行する。

## 動作と検証

`UserPromptSubmit` で会話 ID とターン ID ごとに開始時刻を記録し、
`notify` の `agent-turn-complete` で経過時間を判定して Discord REST API に投稿する。
同じターンへの追加入力で開始時刻をリセットしない。
中断時は記録を削除し、完了イベントの重複でも再通知しない。
設定前から実行中だった回答は、開始時刻がないため通知しない。
プロセス間で共通の単調増加時計を使うため、時計の時刻調整に影響されない。

通知にはマシン名・作業場所・セッション名・所要時間・直前のプロンプトを載せる。
プロンプトは完了イベントの `input-messages` の最後の項目を使い、通知全体が
Discord の 2,000 文字制限に収まるよう末尾を省略する。
セッション名は Codex 内部のキャッシュ `$CODEX_HOME/session_index.jsonl`
（既定は `~/.codex/session_index.jsonl`）から読み、取得できない場合はセッション ID を表示する。
メンションは `mention_user_id` のユーザーだけ許可する。

通知は 1 回だけ送信を試み、失敗は標準エラーへ記録する。
自動再送はしない。送信失敗で Codex の処理を止めない。
通常の送信タイムアウトは 10 秒。強制終了で残った `state/` 内のファイルは、
実行中の回答がないときに削除できる。

実際の Discord へ送らずに検証する:

```sh
python3 -m unittest discover -s "$HOME/.codex/discord-notify" -p 'test_*.py' -v
```

仕様: [Codex hooks](https://developers.openai.com/ja-JP/docs/hooks)、
[Codex notify](https://developers.openai.com/ja-JP/docs/config-file/config-advanced#通知)、
[Discord messages](https://docs.discord.com/developers/resources/message#create-message)。
