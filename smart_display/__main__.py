"""Opt-in modern display: python -m smart_display --demo."""
import argparse
from datetime import datetime
import os
from pathlib import Path
import time

from .core import DisplayConfig, RefreshTask
from .providers import configured_providers


class DisplayApp:
    def __init__(self, root, config, providers, *, demo=False):
        import tkinter as tk
        self.root = root
        self.tasks = {name: RefreshTask(fetch) for name, fetch in providers.items()}
        self.next_refresh = {name: 0.0 for name in providers}
        self.screen = "Clock"
        self.closed = False
        self.after_id = None
        root.title("Smart Display · Demo" if demo else "Smart Display")
        root.geometry(f"{config.width}x{config.height}")
        root.attributes("-fullscreen", config.fullscreen)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        navigation = tk.Frame(root)
        navigation.grid(row=0, column=0, sticky="ew")
        for name in ("Clock", "Weather", "Instagram"):
            tk.Button(navigation, text=name, command=lambda name=name: self.show(name)).pack(side="left", padx=4, pady=4)
        tk.Button(navigation, text="Close", command=self.close).pack(side="right", padx=4)
        self.value = tk.Label(root, text="", font=("Arial", 32), justify="center")
        self.value.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        self.status = tk.Label(root, text="")
        self.status.grid(row=2, column=0, sticky="ew", pady=8)
        root.bind("<Configure>", self.resize)
        root.bind("<Escape>", lambda event: self.close())
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.tick()

    def resize(self, event):
        if event.widget == self.root:
            self.value.configure(font=("Arial", max(12, min(64, event.width // 24))), wraplength=max(160, event.width - 24))

    def show(self, screen):
        self.screen = screen

    def tick(self):
        if self.closed:
            return
        now = time.monotonic()
        for name, task in self.tasks.items():
            task.poll()
            if now >= self.next_refresh[name] and task.start():
                self.next_refresh[name] = now + (60 if name == "Weather" else 20)
        if self.screen == "Clock":
            self.value.configure(text=datetime.now().strftime("%H:%M:%S\n%d %B %Y"))
            self.status.configure(text="Local time")
        elif self.screen not in self.tasks:
            self.value.configure(text=f"{self.screen} is not configured")
            self.status.configure(text="The clock remains available. See docs/modernisation.md for setup.")
        else:
            snapshot = self.tasks[self.screen].snapshot
            updated = f" · Updated {snapshot.updated_at.astimezone():%H:%M:%S}" if snapshot.updated_at else ""
            self.value.configure(text=snapshot.text)
            self.status.configure(text=snapshot.status + updated)
        self.after_id = self.root.after(100, self.tick)

    def close(self):
        if self.closed:
            return
        self.closed = True
        for task in self.tasks.values():
            task.close()
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Use bundled sample data without credentials or network calls.")
    parser.add_argument("--windowed", action="store_true", help="Disable fullscreen mode.")
    args = parser.parse_args(argv)
    try:
        if args.demo:
            config = DisplayConfig()
        else:
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).resolve().parent.parent / ".env")
            config = DisplayConfig.from_env(os.environ)
        if args.windowed:
            from dataclasses import replace
            config = replace(config, fullscreen=False)
    except ValueError as error:
        parser.error(str(error))
    import tkinter as tk
    root = tk.Tk()
    DisplayApp(root, config, configured_providers(config, demo=args.demo), demo=args.demo)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
