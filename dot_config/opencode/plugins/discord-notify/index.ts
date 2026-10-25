import { Plugin } from "@opencode/plugin"
import { readFile } from "node:fs/promises"
import { hostname } from "node:os"
import path from "node:path"
import { fileURLToPath } from "node:url"

const configFile = path.join(path.dirname(fileURLToPath(import.meta.url)), "config.json")

type Settings = {
  readonly bot_token: string
  readonly channel_id: string
  readonly mention_user_id: string
  readonly threshold_seconds: number
}

// The public stream frames every event as { type, created, data }.
type ServerEvent = {
  readonly type: string
  readonly created: number
  readonly data?: { readonly sessionID?: string }
}

const started = new Map<string, number>()
let configMissing = false

function snowflake(record: Record<string, unknown>, key: string): string {
  const value = record[key]
  if (typeof value !== "string" || !/^\d{1,20}$/.test(value) || !(0n < BigInt(value) && BigInt(value) < 2n ** 64n))
    throw new Error(`${key} must be a Discord snowflake ID`)
  return value
}

function parseSettings(text: string): Settings {
  const data: unknown = JSON.parse(text)
  if (typeof data !== "object" || data === null) throw new Error("config.json must contain an object")
  const record = data as Record<string, unknown>
  const token = record.bot_token
  if (typeof token !== "string" || !token.trim() || /\s/.test(token))
    throw new Error("bot_token must be a nonempty string without whitespace")
  const threshold = record.threshold_seconds ?? 600
  if (!Number.isInteger(threshold) || (threshold as number) <= 0)
    throw new Error("threshold_seconds must be a positive integer")
  return {
    bot_token: token,
    channel_id: snowflake(record, "channel_id"),
    mention_user_id: snowflake(record, "mention_user_id"),
    threshold_seconds: threshold as number,
  }
}

async function loadSettings(): Promise<Settings | undefined> {
  try {
    return parseSettings(await readFile(configFile, "utf8"))
  } catch (error) {
    if ((error as NodeJS.ErrnoException)?.code !== "ENOENT") throw error
    if (!configMissing) {
      console.error(`OpenCode Discord notification disabled: create ${configFile}`)
      configMissing = true
    }
    return undefined
  }
}

function truncate(text: string, limit: number): string {
  const points = Array.from(text)
  return points.length <= limit ? text : points.slice(0, limit - 1).join("") + "…"
}

function lastPrompt(messages: readonly { readonly type?: string; readonly text?: unknown }[]): string {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index]
    if (message?.type === "user" && typeof message.text === "string" && message.text.trim()) return message.text
  }
  return "テキストなし"
}

async function send(
  settings: Settings,
  cwd: string,
  title: string,
  elapsed: number,
  prompt: string,
): Promise<void> {
  const content = [
    `<@${settings.mention_user_id}> OpenCode の回答が完了した。`,
    `マシン: ${truncate(hostname(), 128)}`,
    `作業場所: ${truncate(cwd, 300)}`,
    `セッション: ${truncate(title, 160)}`,
    `所要時間: ${Math.floor(elapsed / 60)} 分 ${Math.floor(elapsed % 60)} 秒`,
    "",
    "直前のプロンプト:",
    prompt,
  ].join("\n")
  const response = await fetch(`https://discord.com/api/v10/channels/${settings.channel_id}/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bot ${settings.bot_token}`,
      "Content-Type": "application/json; charset=utf-8",
      "User-Agent": "OpenCodeDiscordNotify/1.0",
    },
    body: JSON.stringify({
      content: truncate(content, 2000),
      allowed_mentions: { parse: [], users: [settings.mention_user_id] },
    }),
    signal: AbortSignal.timeout(10_000),
  })
  if (!response.ok) throw new Error(`Discord returned HTTP ${response.status}`)
  await response.body?.cancel()
}

export default Plugin.define({
  id: "discord-notify",
  setup(ctx) {
    const controller = new AbortController()
    void (async () => {
      try {
        for await (const raw of ctx.event.subscribe({ signal: controller.signal })) {
          const event = raw as unknown as ServerEvent
          const sessionID = event.data?.sessionID
          if (typeof sessionID !== "string") continue
          switch (event.type) {
            case "session.execution.started":
              started.set(sessionID, event.created)
              break
            case "session.execution.succeeded":
            case "session.execution.failed":
            case "session.execution.interrupted": {
              const start = started.get(sessionID)
              started.delete(sessionID)
              // Only a completed answer notifies; failures and interrupts just drop the start time.
              if (event.type !== "session.execution.succeeded" || start === undefined) break
              void (async () => {
                const settings = await loadSettings()
                if (!settings) return
                const elapsed = (event.created - start) / 1000
                if (elapsed < settings.threshold_seconds) return
                const session = await ctx.session.get({ sessionID })
                // Subagent sessions are part of the parent answer; only the session the user drives notifies.
                if (session.parentID) return
                // Every location runs this plugin and sees every event, and session.execution.* has no
                // location. The session's location picks the one notifier; dedupe would need shared state.
                if (session.location.directory !== ctx.location.directory) return
                const messages = await ctx.session.context({ sessionID })
                await send(settings, session.location.directory, session.title ?? sessionID, elapsed, lastPrompt(messages))
              })().catch((error) => {
                console.error(`OpenCode Discord notification failed: ${error}`)
              })
              break
            }
            case "session.deleted":
              started.delete(sessionID)
              break
          }
        }
      } catch (error) {
        if (!controller.signal.aborted) console.error(`OpenCode Discord notification stream failed: ${error}`)
      }
    })()
    return () => controller.abort()
  },
})
