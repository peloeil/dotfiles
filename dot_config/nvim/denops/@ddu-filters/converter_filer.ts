import {
  BaseFilter,
  type FilterArguments,
} from "jsr:@shougo/ddu-vim@11.3.0/filter";
import { dirname, join } from "jsr:@std/path@1";

type Params = Record<never, never>;

// Follow nvim-tree's Git symbols, with staged changes before unstaged changes.
function gitMarker(status: string): string {
  if (status === "??") return "★";
  if (/U|AA|DD/.test(status)) return "";
  return [...status].map((code, index) => {
    if (code === " ") return "";
    if (code === "R") return "➜";
    if (code === "D") return "";
    return index === 0 ? "✓" : "✗";
  }).join("");
}

async function git(
  path: string,
  ...args: string[]
): Promise<string | undefined> {
  try {
    const result = await new Deno.Command("git", {
      args: ["-C", path, ...args],
      stdout: "piped",
      stderr: "null",
    }).output();
    return result.success ? new TextDecoder().decode(result.stdout) : undefined;
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) return undefined;
    throw error;
  }
}

async function gitStatuses(path: string): Promise<Map<string, string>> {
  const statuses = new Map<string, string>();
  const root = (await git(path, "rev-parse", "--show-toplevel"))?.replace(
    /\n$/,
    "",
  );
  if (!root) return statuses;

  // One status query per batch, including files inside untracked directories.
  const output = await git(
    root,
    "status",
    "--porcelain=v1",
    "-z",
    "--untracked-files=all",
  );
  const records = (output ?? "").split("\0");
  for (let index = 0; index < records.length; index++) {
    const record = records[index];
    if (!record) continue;
    const status = record.slice(0, 2);
    const file = join(root, record.slice(3));
    statuses.set(file, status);
    for (
      let parent = dirname(file);
      parent !== root && parent !== dirname(parent);
      parent = dirname(parent)
    ) {
      statuses.set(parent, " *");
    }
    // In -z output the destination precedes the original path for renames/copies.
    if (/[RC]/.test(status)) index++;
  }
  return statuses;
}

export class Filter extends BaseFilter<Params> {
  override async filter(
    { items, context, sourceOptions }: FilterArguments<Params>,
  ) {
    const basePath = sourceOptions.path.length
      ? sourceOptions.path
      : context.path;
    const path = typeof basePath === "string" ? basePath : context.cwd;
    const statuses = await gitStatuses(path || context.cwd);
    for (const item of items) {
      const status = statuses.get((item.action as { path: string }).path);
      // icon_filename already adds one space per level; make it two.
      const padding = " ".repeat(item.__level);
      const display = padding + (item.display ?? item.word).trimEnd();
      for (const highlight of item.highlights ?? []) {
        highlight.col += padding.length;
      }
      const icon = item.highlights!.find((highlight) =>
        highlight.name === "column-icons-icon"
      )!;
      // icon_filename uses byte offsets and one space between icon and name.
      const prefix = new TextDecoder().decode(
        new TextEncoder().encode(display).subarray(0, icon.col + icon.width),
      );
      const marker = gitMarker(status ?? "");
      // Reserve two cells on every row so both icons and filenames stay aligned.
      const markerPadding = " ".repeat(2 - marker.length);
      item.display = `${prefix}${markerPadding}${marker} ${
        display.slice(prefix.length)
      }`;
      if (status) {
        const group = /U|AA|DD/.test(status)
          ? "DiagnosticError"
          : status === "??"
          ? "DiagnosticInfo"
          : status.includes("D")
          ? "DiagnosticError"
          : status[1] !== " "
          ? "DiagnosticWarn"
          : "DiagnosticOk";
        (item.highlights ??= []).push({
          name: "filer_git_status",
          hl_group: group,
          col: icon.col + icon.width + markerPadding.length + 1,
          width: new TextEncoder().encode(marker).length,
        });
      }
    }
    return items;
  }

  override params(): Params {
    return {};
  }
}
