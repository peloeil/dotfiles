# OpenCode の Discord 完了通知

既定では 600 秒以上かかった回答の完了時に、指定ユーザーをメンションして通知する。
所要時間には tool 実行や承認待ちも含む。しきい値に達した時点では投稿しない。

OpenCode の V2 plugin として動き、`~/.config/opencode/plugins/` から自動で読み込まれる。
追加のパッケージは不要。

このディレクトリの `config.json` は Codex の完了通知とも共用する唯一の設定で、
Codex は `~/.codex/discord-notify/config.json` を読まない。

## 設定する

chezmoi でコードと `config.example.json` を配置した後、各マシンで設定する。
Bot には対象チャンネルの閲覧・送信権限が必要。

初回は設定例をコピーして編集する。既存の `config.json` がある場合はコピーせず、
そのファイルを編集する。

```sh
install -m600 "$HOME/.config/opencode/plugins/discord-notify/config.example.json" \
  "$HOME/.config/opencode/plugins/discord-notify/config.json"
$EDITOR "$HOME/.config/opencode/plugins/discord-notify/config.json"
```

`config.json` に次を設定する。

- `bot_token`: 投稿する Bot のトークン。
- `channel_id`: 投稿先チャンネル ID。
- `mention_user_id`: メンションするユーザー ID。
- `threshold_seconds`: 通知のしきい値。初期値は 600 秒。

Bot トークンを含む `config.json` は暗号化しても chezmoi の管理対象に加えない。
`.chezmoiignore` で除外している。トークンは各マシンで設定するか、
既存の設定ファイルを別途安全に転送する。
以前の Codex 版の `~/.codex/discord-notify/config.json` がある場合は、
この場所へ移動してから元のファイルを削除する。
設定は通知のたびに読み直すため、変更に OpenCode の再起動は要らない。

## 動作と検証

`session.execution.started` でセッションごとに開始時刻を記録し、
`session.execution.succeeded` でイベントの時刻から経過時間を判定して Discord REST API に投稿する。
サブエージェントの子セッションは完了イベントを出すが、親セッションの回答に含まれるため通知しない。
失敗と中断では開始時刻を捨て、通知しない。
設定前から実行中だった回答は、開始時刻がないため通知しない。

通知にはマシン名・作業場所・セッション名・所要時間・直前のプロンプトを載せる。
プロンプトはセッションの最後の user メッセージを使い、通知全体が Discord の 2,000 文字制限に収まるよう末尾を省略する。
メンションは `mention_user_id` のユーザーだけ許可する。

通知は 1 回だけ送信を試み、失敗は OpenCode のログへ記録する。
自動再送はしない。送信失敗で回答処理を止めない。
送信タイムアウトは 10 秒。

`config.json` がない場合は起動時に一度だけログへ記録し、通知しない。
`threshold_seconds` を短くして長めの回答を 1 回実行し、実際の投稿を確認する。

仕様: [OpenCode plugins](https://opencode.ai/v2/docs/build/plugins)、
[Discord messages](https://docs.discord.com/developers/resources/message#create-message)。
