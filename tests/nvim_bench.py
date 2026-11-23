"""Compare Neovim startup time across configs and fail if any config prints errors.

Usage: python3 tests/nvim_bench.py [--runs N] [--file PATH] [CONFIG ...]
CONFIG is an NVIM_APPNAME, or "clean" for `nvim --clean`.
"""

import argparse
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def command(config: str, file: Path, *extra: str) -> tuple[list[str], dict[str, str]]:
    env = dict(os.environ)
    args = ["nvim", "--headless", *extra]
    if config == "clean":
        args.insert(1, "--clean")
    else:
        env["NVIM_APPNAME"] = config
    return [*args, "+qa!", str(file)], env


def errors(config: str, file: Path) -> str:
    args, env = command(config, file)
    result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
    return (result.stdout + result.stderr).strip()


def startup_ms(config: str, file: Path, log: Path) -> float:
    log.unlink(missing_ok=True)
    args, env = command(config, file, "--startuptime", str(log))
    subprocess.run(args, env=env, capture_output=True, check=True, timeout=60)
    started = [line for line in log.read_text().splitlines() if "NVIM STARTED" in line]
    return float(started[-1].split()[0])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--file", type=Path, default=REPO / "dot_config/nvim-next/init.lua")
    parser.add_argument("configs", nargs="*", default=["nvim-next", "nvim", "clean"])
    args = parser.parse_args()

    failed = False
    for config in args.configs:
        if output := errors(config, args.file):
            print(f"{config}: startup output\n{output}", file=sys.stderr)
            failed = True
    if failed:
        return 1

    times: dict[str, list[float]] = {config: [] for config in args.configs}
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "startuptime.log"
        # Interleave configs so background load affects each one equally.
        for _ in range(args.runs):
            for config in args.configs:
                times[config].append(startup_ms(config, args.file, log))

    print(f"{'config':<12} {'min':>7} {'median':>7} {'max':>7}  (ms, {args.runs} runs, {args.file.name})")
    for config, values in times.items():
        print(f"{config:<12} {min(values):7.1f} {statistics.median(values):7.1f} {max(values):7.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
