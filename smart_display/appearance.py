"""Read the desktop preference without modifying the host's appearance settings."""
import re
import subprocess


def read_system_theme():
    # ReadOne is the current portal method; Read supports older Pi desktops.
    for method in ("ReadOne", "Read"):
        try:
            result = subprocess.run(
                ["gdbus", "call", "--session", "--dest", "org.freedesktop.portal.Desktop",
                 "--object-path", "/org/freedesktop/portal/desktop", "--method",
                 f"org.freedesktop.portal.Settings.{method}",
                 "org.freedesktop.appearance", "color-scheme"],
                capture_output=True, text=True, timeout=1,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        preference = re.search(r"uint32\s+([0-9]+)", result.stdout)
        if result.returncode == 0 and preference:
            return "light" if preference.group(1) == "2" else "dark"
    # Some older Linux desktops have GTK settings but no appearance portal.
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True, timeout=1,
        )
        if result.returncode == 0 and "prefer-light" in result.stdout:
            return "light"
    except (OSError, subprocess.TimeoutExpired):
        pass
    # Preserve the original display appearance if the desktop has no preference.
    return "dark"
