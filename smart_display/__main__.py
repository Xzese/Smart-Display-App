"""Opt-in modern display: python -m smart_display --demo."""
import argparse
import os
from pathlib import Path

from .core import DisplayConfig
from .providers import configured_providers
from .ui import DisplayApp


def main(argv=None, *, env_path=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Use bundled sample data without credentials or network calls.")
    parser.add_argument("--windowed", action="store_true", help="Disable fullscreen mode.")
    args = parser.parse_args(argv)
    env_path = Path(env_path) if env_path is not None else Path(__file__).resolve().parent.parent / ".env"
    try:
        if args.demo:
            config = DisplayConfig()
        else:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            config = DisplayConfig.from_env(os.environ)
        if args.windowed:
            from dataclasses import replace
            config = replace(config, fullscreen=False)
    except ValueError as error:
        parser.error(str(error))
    import tkinter as tk
    root = tk.Tk()

    def save_theme(theme):
        if not args.demo:
            from dotenv import set_key
            set_key(str(env_path), "DISPLAY_THEME", theme)

    DisplayApp(root, config, configured_providers(config, demo=args.demo),
               demo=args.demo, save_theme=save_theme)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
