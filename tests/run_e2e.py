"""Run all tests on a fresh Xvfb display with a fullscreen-capable window manager."""
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time

from Xlib import display


def stop(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    missing = [name for name in ("Xvfb", "openbox") if not shutil.which(name)]
    if missing:
        raise SystemExit("Required desktop test tools missing: " + ", ".join(missing))
    project = Path(__file__).resolve().parents[1]
    xvfb = wm = None
    try:
        xvfb = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "1920x1080x24", "-nolisten", "tcp", "-ac"],
            stdout=subprocess.PIPE, text=True,
        )
        if not select.select([xvfb.stdout], [], [], 5)[0]:
            raise RuntimeError("Xvfb did not become ready")
        number = xvfb.stdout.readline().strip()
        if not number.isdigit():
            raise RuntimeError("Xvfb failed to start")
        env = {**os.environ, "DISPLAY": f":{number}"}
        command = ["openbox", "--sm-disable"]
        if os.environ.get("SMART_DISPLAY_OPENBOX_CONFIG"):
            command += ["--config-file", os.environ["SMART_DISPLAY_OPENBOX_CONFIG"]]
        wm = subprocess.Popen(command, env=env)
        connection = display.Display(env["DISPLAY"])
        try:
            atom = connection.intern_atom("_NET_SUPPORTING_WM_CHECK")
            deadline = time.monotonic() + 5
            while not connection.screen().root.get_full_property(atom, 0):
                if wm.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Window manager did not become ready")
                time.sleep(0.05)
        finally:
            connection.close()
        return subprocess.call([sys.executable, "-m", "pytest", *sys.argv[1:]], cwd=project, env=env)
    finally:
        stop(wm)
        stop(xvfb)


if __name__ == "__main__":
    raise SystemExit(main())
