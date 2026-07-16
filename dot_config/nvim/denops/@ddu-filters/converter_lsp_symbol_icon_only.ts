import {
  BaseFilter,
  type DduItem,
} from "https://deno.land/x/ddu_vim@v3.8.1/types.ts";

type Params = Record<string, never>;

const byteLength = (text: string): number =>
  new TextEncoder().encode(text).length;

export class Filter extends BaseFilter<Params> {
  override filter(args: {
    items: DduItem[];
  }): Promise<DduItem[]> {
    return Promise.resolve(args.items.map((item) => {
      const display = item.display ?? item.word;
      const match = display.match(/^(\S+\s+)(\[[^\]]+\]\s+)/);
      if (!match) {
        return item;
      }

      const removedWidth = byteLength(match[2]);
      item.display = match[1] + display.slice(match[0].length);
      item.highlights = (item.highlights ?? []).map((highlight) => {
        if (
          highlight.name.startsWith(
            "ddu-filter-converter_lsp_symbol-",
          )
        ) {
          return {
            ...highlight,
            width: Math.max(0, highlight.width - removedWidth),
          };
        }

        return {
          ...highlight,
          col: Math.max(1, highlight.col - removedWidth),
        };
      });

      return item;
    }));
  }

  override params(): Params {
    return {};
  }
}
