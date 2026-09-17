"""Check real terminal save prompts: python3 tests/check_nvim_save.py."""

import fcntl
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import tempfile
import termios
import time


source = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="nvim-save-") as temporary:
    directory = Path(temporary)
    document = directory / "sample.txt"
    document.write_text("hello\n")
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    process = subprocess.Popen(
        [
            "nvim", "-n", "-i", "NONE",
            "-u", str(source / "dot_config/nvim/lua/options.lua"),
            "--cmd", "set background=dark",
            "+set noundofile", str(document),
        ],
        stdin=slave, stdout=slave, stderr=slave,
        env=dict(
            os.environ, TERM="xterm-256color", LC_ALL="C",
            NVIM_LOG_FILE=str(directory / "nvim.log"),
            XDG_STATE_HOME=str(directory / "state"),
        ),
    )
    os.close(slave)

    def read_screen():
        output = b""
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], max(0, deadline - time.monotonic()))
            if ready:
                chunk = os.read(master, 65536)
                output += chunk
                # Answer terminal queries so startup does not produce unrelated warnings.
                if b"\x1b[5n" in chunk:
                    os.write(master, b"\x1b[0n")
                if b"\x1b]11;?" in chunk:
                    os.write(master, b"\x1b]11;rgb:0000/0000/0000\x1b\\")
        return output

    try:
        startup = read_screen()
        assert b"Press ENTER" not in startup, startup
        for count in range(1, 4):
            os.write(master, b"A edit\x1b:w\r")
            output = read_screen()
            assert b"Press ENTER" not in output, "Saving stopped at a hit-enter prompt"
            assert document.read_text() == "hello" + " edit" * count + "\n"

        os.write(master, b":set readonly\r")
        read_screen()
        os.write(master, b":w\r")
        output = read_screen()
        assert b"E45" in output, "Readonly write error was hidden"
    finally:
        process.terminate()
        process.wait(timeout=5)
        os.close(master)

print("OK: three terminal saves require no ENTER; write errors remain visible")
