import { type Dpp } from "jsr:@shougo/dpp-vim@4.5.0/dpp";
import {
  type ContextBuilder,
  type Plugin,
} from "jsr:@shougo/dpp-vim@4.5.0/types";
import {
  BaseConfig,
  type ConfigArguments,
  type ConfigReturn,
} from "jsr:@shougo/dpp-vim@4.5.0/config";
import { type Toml } from "jsr:@shougo/dpp-ext-toml";
import { type LazyMakeStateResult } from "jsr:@shougo/dpp-ext-lazy";
import { type Denops } from "jsr:@denops/core@7.0.1";
import * as fn from "jsr:@denops/std@7.6.0/function";
import { expandGlobSync } from "jsr:@std/fs@1.0.19";


function gatherCheckFiles(path: string, glob: string): string[] {
  const checkFiles: string[] = [];
  for (const file of expandGlobSync(glob, { root: path, globstar: true })) {
    checkFiles.push(file.path);
  }
  return checkFiles;
}

export class Config extends BaseConfig {
  override async config(args: ConfigArguments): Promise<ConfigReturn> {
    // dpp-protocol-git, dpp-ext-installer の設定
    args.contextBuilder.setGlobal({
      protocols: ["git"],
      protocolParams: {
        git: {
          enablePartialClone: true,
        },
      },
    });

    const [context, options] = await args.contextBuilder.get(args.denops);
    const configDir = await fn.expand(args.denops, "~/.config/nvim");
    const tomlDir = configDir + "/toml/";

    const noLazyPlugins = await args.dpp.extAction(
      args.denops,
      context,
      options,
      "toml",
      "load",
      {
        path: tomlDir + "no_lazy.toml",
        options: {
          lazy: false,
        },
      },
    ) as Toml;

    const lazyPlugins = await args.dpp.extAction(
      args.denops,
      context,
      options,
      "toml",
      "load",
      {
        path: tomlDir + "lazy.toml",
        options: {
          lazy: true,
        },
      },
    ) as Toml;

    const dppPlugins = await args.dpp.extAction(
      args.denops,
      context,
      options,
      "toml",
      "load",
      {
        path: tomlDir + "dpp.toml",
        options: {
          lazy: false,
        },
      },
    ) as Toml;

    const dduPlugins = await args.dpp.extAction(
      args.denops,
      context,
      options,
      "toml",
      "load",
      {
        path: tomlDir + "ddu.toml",
        options: {
          lazy: true,
        },
      },
    ) as Toml;

    const record: Record<string, Plugin> = {};

    for (const plugin of noLazyPlugins.plugins) {
      record[plugin.name] = plugin;
    }
    for (const plugin of lazyPlugins.plugins) {
      record[plugin.name] = plugin;
    }
    for (const plugin of dppPlugins.plugins) {
      record[plugin.name] = plugin;
    }
    for (const plugin of dduPlugins.plugins) {
      record[plugin.name] = plugin;
    }

    const lazyResult = await args.dpp.extAction(
      args.denops,
      context,
      options,
      "lazy",
      "makeState",
      {
        plugins: Object.values(record),
      },
    ) as LazyMakeStateResult;

    return {
      checkFiles: gatherCheckFiles(configDir, "**/*.@(ts|toml|lua)"),
      plugins: Object.values(record),
      stateLines: lazyResult.stateLines,
    };
  }
}
