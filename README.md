# dotfiles

自分の Linux x86_64 環境を復元・更新するためのリポジトリ。
chezmoi で設定を配布し、mise・uv・Codex standalone installer でツールを入れる。`desktop = true`（既定）なら Xorg / i3 環境も含む。

## 新しいマシンに復元する

一般ユーザーで作業する。

- 前提: ネットワーク、`curl`、`git`、`tar`、`sudo`（`apt-get` / `pacman` / `emerge`）。
- Gentoo でデスクトップを入れる場合は `app-i18n/mozc` の `fcitx5` USE フラグを有効にする。
- SSH 先で使う場合、Nerd Font は接続元の端末で設定する。

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin" init peloeil
export PATH="$HOME/.local/bin:$PATH"
```

初期質問では `desktop`（既定 `true`）、`denopsSharedServer`（既定 `false`）、`zennPreview`（既定 `false`）、Git の通常/研究用メール、研究用ディレクトリ（既定 `~/workspace/university/laboratory/research/`）、名前を `~/.config/chezmoi/chezmoi.toml` に保存する。研究用ディレクトリ配下では研究用メールへ自動で切り替わる。

デスクトップなしで始める場合は `init peloeil` の後ろに `--promptBool 'Install desktop environment=false'` を付ける。

```sh
chezmoi diff
chezmoi apply --dry-run
chezmoi apply
```

完了後は新しい端末を開く。fish は `~/.local/bin/mise exec -- fish` で起動できる（ログインシェルは自動では変えない）。

### リポジトリ外で用意するもの

`desktop = false` では壁紙・モニター設定・Sunshine は不要。

| 対象 | 必要な作業 |
| --- | --- |
| 壁紙 | `~/media/pictures/wallpapers/neko.jpg` を置くか i3 の指定を変える |
| モニター設定 | `~/.config/i3/monitor-hotplug.sh` を用意するか i3 の起動処理・キー割り当てを変える |
| Sunshine | 本体と systemd user service を用意し、`~/.config/sunshine/sunshine.conf` の GPU・出力指定を合わせる |
| Podman | 本体を OS パッケージで入れる（自動導入しない）。`podman-compose` は mise で入る |
| AI ツール | Codex / Claude Code / Antigravity CLI を認証する。OpenCode は `opencode auth login openai`（さくら併用時は `opencode auth login sakura --method key`） |
| Antigravity | `agy` の `/config` で `Enable Telemetry` を切る（アカウントごとの設定のため毎回1度行う） |
| Discord 通知 | `~/.config/opencode/plugins/discord-notify/config.json` を用意する（Codex 版も共用） |
| Zenn プレビュー | 下記の手順で記事リポジトリと Tailscale を用意する |

## 構成を切り替える

`chezmoi edit-config` の `[data]` を変えて `chezmoi apply` する。

- **`desktop`**: `true` → `false` に変えても、導入済みパッケージや除外した設定ファイルは自動では消さない。
- **`denopsSharedServer`**: `true` で `denops-shared-server.service` を起動し、Neovim 間で Denops を使い回す（systemd user manager が必要）。接続先は `127.0.0.1:32123`（`denopsServerPort` で変更可）。認証がないため共有マシンでは無効のまま使う。
- **`zennPreview`**: `true` で `zenn-preview.service`（`:8000` で `articles/`）と `zenn-notes.service`（`:8001` で `notes/`）を Tailscale IPv4 で待ち受ける（systemd user manager が必要）。事前に `~/workspace/zenn` で `npm ci` と Tailscale 接続を済ませる。ログアウト中も動かす場合は `sudo loginctl enable-linger "$USER"` を実行する。

## AI 設定の運用メモ

- 共通の応答方針と自作スキルは `dot_config/opencode/` 側だけを編集する（Codex / Claude Code / Antigravity CLI も同じ配置先を参照する）。
- 外部から導入する plugin 本体・キャッシュ・認証情報は管理しない。更新は各ツールに任せる（OpenCode は起動時、Claude Code は `autoUpdate`、Codex は `codex plugin marketplace upgrade`）。
- 外部スキルは `.chezmoiexternal.toml` で取得し、`chezmoi apply` 時に前回から 1 時間以上経っていれば更新を確認する（即時更新は `chezmoi -R apply ~/.config/opencode/skills`）。`natural-japanese` と `yomiyasu` は Gemini には不要なため `dot_gemini/config/skills.json.tmpl` の `exclude` で外している。
- 承認省略は各ツールで揃えており、信頼できないプロジェクトでは個別に見直す。
