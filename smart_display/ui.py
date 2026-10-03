"""Original wide-display presentation backed by the modern refresh lifecycle."""
from datetime import datetime
from pathlib import Path
import time

from .appearance import read_system_theme
from .core import RefreshTask


class DisplayApp:
    def __init__(self, root, config, providers, *, demo=False, save_theme=None):
        import tkinter as tk
        from tkinter import font
        from PIL import Image

        self.root, self.config, self.demo = root, config, demo
        self.save_theme = save_theme
        self.tasks = {name: RefreshTask(fetch) for name, fetch in providers.items()}
        self.next_refresh = {name: 0.0 for name in providers}
        self.system_appearance = RefreshTask(read_system_theme)
        self.next_appearance = 0.0
        self.theme = None
        self.theme_mode = tk.StringVar(root, config.theme)
        self.settings_notice = ""
        self.screen = "Clock"
        self.closed = False
        self.after_id = None
        self._layout_key = None
        self._visibility_key = None
        self._font = font.Font(root=root)
        families = {family.lower() for family in font.families(root)}
        self.family = config.text_font if config.text_font.lower() in families else "Arial"
        self.sources = {}
        assets = Path(__file__).resolve().parent.parent / "images"
        for name, filename in {"Settings": "Cog", "Clock": "Clock", "Instagram": "Camera", "Weather": "Weather"}.items():
            with Image.open(assets / f"{filename}.png") as image:
                self.sources[name] = image.convert("RGBA")
        self.images = {}

        root.title("Smart Display · Demo" if demo else "Smart Display")
        width = config.width or round(root.winfo_screenwidth() * 0.75)
        height = config.height or round(root.winfo_screenheight() * 0.75)
        root.geometry(f"{width}x{height}")
        root.attributes("-fullscreen", config.fullscreen)
        if config.fullscreen:
            root.configure(cursor="none")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.content = tk.Frame(root)
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.grid_propagate(False)
        self.content.columnconfigure(0, weight=1, uniform="content")
        self.content.columnconfigure(1, weight=4, uniform="content")
        self.content.rowconfigure(0, weight=1, uniform="content_rows")
        self.content.rowconfigure(1, weight=3, uniform="content_rows")
        self.header = tk.Frame(self.content)
        self.header.grid(row=0, column=1, sticky="nsew")
        self.header.grid_propagate(False)
        self.header.rowconfigure(0, weight=1)
        for column, weight in enumerate((2, 4, 2)):
            self.header.columnconfigure(column, weight=weight, uniform="header")
        self.body = tk.Frame(self.content)
        self.body.grid(row=1, column=1, sticky="nsew")
        self.body.grid_propagate(False)
        self.nav_frame = tk.Frame(root)
        self.nav_frame.grid(row=0, column=1, rowspan=2, sticky="ns")
        self.nav_frame.grid_propagate(False)
        self.nav_frame.columnconfigure(0, weight=1)
        for row in (1, 3, 5):
            self.nav_frame.rowconfigure(row, weight=1)
        self.navigation = {}
        for name in self.sources:
            self.navigation[name] = tk.Button(
                self.nav_frame, text=name, command=lambda name=name: self.show(name),
                bd=0, highlightthickness=0, takefocus=True,
            )
        self.logo = tk.Label(self.content, bd=0)
        self.logo.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=8, pady=8)
        self.labels = {name: tk.Label(self.header if name == "title" else self.body,
                                      bd=0, anchor="center", justify="center") for name in (
            "title", "primary", "date", "account", "now_label", "now_temp", "now_conditions",
            "future_label", "future_temp", "future_conditions", "message", "appearance", "details",
        )}
        self.value = self.labels["primary"]
        self.status = tk.Label(root, bd=0, anchor="center", justify="center")
        self.status.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        self.theme_choices = {}
        for name, mode in (("Track system", "system"), ("Light", "light"), ("Dark", "dark")):
            self.theme_choices[mode] = tk.Radiobutton(
                self.body, text=name, variable=self.theme_mode, value=mode, bd=0,
                highlightthickness=0, command=self.change_theme, takefocus=True,
            )
        self.close_button = tk.Button(self.header, text="Close App", command=self.close, bd=1, highlightthickness=0)
        root.bind("<Configure>", self.resize)
        root.bind("<Escape>", lambda event: self.close())
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.apply_theme("dark" if config.theme == "system" else config.theme)
        self.tick()

    def apply_theme(self, theme):
        self.theme = theme
        dark = theme == "dark"
        self.background = ("#505050" if dark else "#e6e6e6") if self.screen == "Settings" else ("#000000" if dark else "#ffffff")
        self.foreground = "#ffffff" if dark else "#000000"
        self.root.configure(bg=self.background)
        for frame in (self.content, self.header, self.body, self.nav_frame):
            frame.configure(bg=self.background)
        for widget in (self.logo, *self.labels.values(), self.status):
            widget.configure(bg=self.background, fg=self.foreground)
        for button in (*self.navigation.values(), self.close_button, *self.theme_choices.values()):
            button.configure(bg=self.background, fg=self.foreground,
                             activebackground="#707070" if dark else "#cccccc",
                             activeforeground=self.foreground)
        for button in self.theme_choices.values():
            button.configure(selectcolor=self.background)
        self.status.configure(fg="#d0d0d0" if dark else "#555555")
        self._layout_key = None
        self.layout()

    def change_theme(self):
        mode = self.theme_mode.get()
        if mode not in {"system", "light", "dark"}:
            return
        if mode == "system":
            self.next_appearance = 0.0
        self.apply_theme(self.effective_theme())
        try:
            if self.save_theme is not None:
                self.save_theme(mode)
            self.settings_notice = "Demo · Changes apply to this session" if self.demo else "Appearance saved"
        except OSError:
            self.settings_notice = "Appearance changed for this session; unable to save it"
        self.render()

    def effective_theme(self):
        mode = self.theme_mode.get()
        if mode != "system":
            return mode
        detected = self.system_appearance.snapshot.text
        return detected if detected in {"light", "dark"} else "dark"

    def resize(self, event):
        if event.widget == self.root:
            self.layout()

    def show(self, screen):
        if screen not in self.sources:
            return
        self.screen = screen
        self.apply_theme(self.effective_theme())
        self.render()

    def image(self, screen, size):
        from PIL import Image, ImageOps, ImageTk
        key = screen, size, self.theme
        if key not in self.images:
            source = self.sources[screen]
            if self.theme == "light":
                source = ImageOps.invert(source.convert("RGB")).convert("RGBA")
                source.putalpha(self.sources[screen].getchannel("A"))
            source = source.copy()
            source.thumbnail((size, size), Image.Resampling.LANCZOS)
            self.images[key] = ImageTk.PhotoImage(source, master=self.root)
            # Keep the cache bounded while resizing a window repeatedly.
            if len(self.images) > 40:
                current = self.images[key]
                self.images = {key: current}
        return self.images[key]

    def fit(self, widget, fraction=0.6, inset=4):
        width, height = widget.winfo_width(), widget.winfo_height()
        if width <= 1 or height <= 1:
            return
        lines = widget.cget("text").splitlines() or [""]
        low, high, best = 6, max(6, round(height * fraction)), 6
        while low <= high:
            size = (low + high) // 2
            self._font.configure(family=self.family, size=size)
            fits = max(self._font.measure(line) for line in lines) <= width - inset
            fits = fits and self._font.metrics("linespace") * len(lines) <= height - 4
            if fits:
                best, low = size, size + 1
            else:
                high = size - 1
        widget.configure(font=(self.family, best), wraplength=max(1, width - inset))
        return best

    def grid_label(self, name, row, column, rowspan=1, columnspan=1):
        self.labels[name].grid(row=row, column=column, rowspan=rowspan,
                               columnspan=columnspan, sticky="nsew", padx=4, pady=2)

    def layout(self):
        width, height = self.root.winfo_width(), self.root.winfo_height()
        key = width, height, self.screen, self.theme, self.has_reading(), tuple(widget.cget("text") for widget in self.labels.values())
        if key == self._layout_key:
            return
        self._layout_key = key
        visibility_key = self.screen, self.has_reading()
        if visibility_key != self._visibility_key:
            for widget in (*self.labels.values(), *self.theme_choices.values(), self.close_button):
                widget.grid_forget()
            for column in range(3):
                self.body.columnconfigure(column, weight=0, uniform="")
            for row in range(3):
                self.body.rowconfigure(row, weight=0, uniform="")
            self.labels["title"].grid(row=0, column=0, columnspan=3, sticky="nsew")
            if self.screen == "Clock":
                self.body.columnconfigure(0, weight=5, uniform="body")
                self.body.columnconfigure(1, weight=1, uniform="body")
                self.body.rowconfigure(0, weight=1)
                self.grid_label("primary", 0, 0)
                self.grid_label("date", 0, 1)
            elif self.screen == "Instagram" and self.has_reading():
                self.body.columnconfigure(0, weight=1)
                self.body.rowconfigure(0, weight=4, uniform="body_rows")
                self.body.rowconfigure(1, weight=1, uniform="body_rows")
                self.grid_label("primary", 0, 0)
                self.grid_label("account", 1, 0)
            elif self.screen == "Weather" and self.has_reading():
                for column, prefix in enumerate(("now", "future")):
                    self.body.columnconfigure(column, weight=1, uniform="body")
                    for row, suffix in enumerate(("label", "temp", "conditions")):
                        self.grid_label(f"{prefix}_{suffix}", row, column)
                for row, weight in enumerate((1, 2, 1)):
                    self.body.rowconfigure(row, weight=weight, uniform="body_rows")
            elif self.screen == "Settings":
                self.labels["title"].grid(row=0, column=1, columnspan=1, sticky="nsew")
                self.close_button.grid(row=0, column=0, sticky="ew", padx=8)
                for column in range(3):
                    self.body.columnconfigure(column, weight=1, uniform="body")
                for row in range(3):
                    self.body.rowconfigure(row, weight=1, uniform="body_rows")
                self.grid_label("appearance", 0, 0, columnspan=3)
                self.grid_label("details", 2, 0, columnspan=3)
                for column, button in enumerate(self.theme_choices.values()):
                    button.grid(row=1, column=column, sticky="nsew", padx=4)
            else:
                self.body.columnconfigure(0, weight=1)
                self.body.rowconfigure(0, weight=1)
                self.grid_label("message", 0, 0)
            self._visibility_key = visibility_key
        button_size = max(26, min(72, round(min(width * 0.045, height * 0.16))))
        self.nav_frame.configure(width=button_size + 12)
        for index, (name, button) in enumerate(self.navigation.items()):
            button.image = self.image(name, button_size)
            button.configure(image=button.image, width=button_size, height=button_size)
            button.grid(row=index * 2, column=0, padx=6, pady=6)
        self.status.configure(font=(self.family, max(7, min(11, round(width / 100)))),
                              wraplength=max(1, width - button_size - 32))
        self.root.update_idletasks()
        logo_size = max(1, round(min(self.logo.winfo_width() * 0.9, self.logo.winfo_height() * 0.8)))
        self.logo.image = self.image(self.screen, logo_size)
        self.logo.configure(image=self.logo.image)
        for name, label in self.labels.items():
            if label.winfo_ismapped():
                fraction = 0.85 if name == "primary" else 0.6
                if name in {"date", "account", "details"}:
                    fraction = 0.3
                self.fit(label, fraction)
        if self.screen == "Settings":
            sizes = [self.fit(button, 0.4, inset=32) for button in self.theme_choices.values()]
            control_size = min((size for size in sizes if size is not None), default=6)
            # Tk's radio indicator also grows with the font; include its real
            # requested size rather than assuming a fixed amount of padding.
            while True:
                for button in self.theme_choices.values():
                    button.configure(font=(self.family, control_size))
                self.root.update_idletasks()
                fits = all(button.winfo_reqwidth() <= button.winfo_width()
                           and button.winfo_reqheight() <= button.winfo_height()
                           for button in self.theme_choices.values())
                if fits or control_size <= 6:
                    break
                control_size -= 1
            self.close_button.configure(font=(self.family, max(8, min(20, round(self.header.winfo_height() / 6)))))

    def has_reading(self):
        return self.screen in self.tasks and self.tasks[self.screen].snapshot.updated_at is not None

    def content_text(self):
        """Text actually shown on the current screen (also useful to assistive tools)."""
        return "\n".join(widget.cget("text") for widget in self.labels.values() if widget.winfo_ismapped() and widget.cget("text"))

    def render(self):
        labels = self.labels
        titles = {"Clock": "Time", "Instagram": "Followers", "Weather": "Weather", "Settings": "Settings"}
        labels["title"].configure(text=titles[self.screen])
        if self.screen == "Clock":
            now = datetime.now()
            labels["primary"].configure(text=now.strftime("%H:%M:%S"))
            labels["date"].configure(text=now.strftime("%d\n%b"))
            self.status.configure(text="Local time")
        elif self.screen == "Settings":
            labels["appearance"].configure(text="Appearance")
            labels["details"].configure(text=f"Appearance: {self.theme.title()} · "
                                        + ("Demo data" if self.demo else "Optional providers are configured in .env"))
            self.status.configure(text=self.settings_notice or ("Demo · Changes apply to this session" if self.demo else "Choose how the display follows your desktop"))
        elif self.screen not in self.tasks:
            labels["message"].configure(text=f"{self.screen} is not configured")
            self.status.configure(text="The clock remains available. See docs/modernisation.md for setup.")
        else:
            snapshot = self.tasks[self.screen].snapshot
            updated = f" · Updated {snapshot.updated_at.astimezone():%H:%M:%S}" if snapshot.updated_at else ""
            self.status.configure(text=snapshot.status + updated)
            if not self.has_reading():
                labels["message"].configure(text=snapshot.text)
            elif self.screen == "Instagram":
                count, _, account = snapshot.text.partition("\n")
                labels["primary"].configure(text=count.removesuffix(" followers"))
                labels["account"].configure(text=account)
            else:
                current, _, forecast = snapshot.text.partition("\n")
                temperature, _, conditions = current.partition(" · ")
                future_label, _, reading = forecast.partition(": ")
                future_temp, _, future_conditions = reading.partition(" · ")
                for name, text in {
                    "now_label": "Now", "now_temp": temperature, "now_conditions": conditions,
                    "future_label": future_label, "future_temp": future_temp, "future_conditions": future_conditions,
                }.items():
                    labels[name].configure(text=text)
        self.layout()

    def tick(self):
        if self.closed:
            return
        now = time.monotonic()
        self.system_appearance.poll()
        if self.theme_mode.get() == "system":
            if now >= self.next_appearance and self.system_appearance.start():
                self.next_appearance = now + 2
            if self.effective_theme() != self.theme:
                self.apply_theme(self.effective_theme())
        for name, task in self.tasks.items():
            task.poll()
            if now >= self.next_refresh[name] and task.start():
                self.next_refresh[name] = now + (60 if name == "Weather" else 20)
        self.render()
        self.after_id = self.root.after(100, self.tick)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.system_appearance.close()
        for task in self.tasks.values():
            task.close()
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.root.destroy()
