import tkinter.ttk as ttk
import tkinter as tk
import json, os, sys, shutil
from pathlib import Path
from PIL import Image, ImageTk
from tkinter import filedialog
from typing import TYPE_CHECKING


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        # For development or when _MEIPASS is not defined
        if TYPE_CHECKING:
            base_path = os.getcwd()  # type: ignore
        base_path = os.getcwd()
    return os.path.join(base_path, relative_path)


class ConfigManager:
    """Handles reading and writing the application configuration."""

    FILE_NAME = "cache.json"
    DEFAULT_CONFIG = {"path": "", "delay": 2.5, "shuffle": False}

    @classmethod
    def read(cls):
        if os.path.exists(cls.FILE_NAME):
            try:
                with open(cls.FILE_NAME, "r") as file:
                    return json.load(file)
            except (json.JSONDecodeError, OSError):
                return cls.DEFAULT_CONFIG.copy()
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def write(cls, data):
        try:
            with open(cls.FILE_NAME, "w") as file:
                json.dump(data, file)
        except OSError as e:
            print(f"Error saving config: {e}")


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.config = ConfigManager.read()
        self.shuffled = self.config.get("shuffle", False)

        try:
            self.wait_time = float(self.config.get("delay", 2.5))
        except ValueError:
            self.wait_time = 2.5

        self.current_image_index = 0
        self.loop_active = False
        self.loop_id = None  # To store the after() callback ID
        self.info_timer_id = None
        self.play_pause = "⏸️"

        self.image_path = Path(self.config.get("path", "."))
        self.files = self.load_images()

        if self.shuffled:
            from random import shuffle

            shuffle(self.files)

        self.configure(bg="black")
        self.attributes("-fullscreen", True)
        self.focus_force()

        self.image_label = tk.Label(self, bg="black")
        self.image_label.pack(expand=True, fill="both")

        self.timer_info_label = tk.Label(self, font=("Segoe UI", 36), bg="black", fg="white")

        self.text_label = tk.Label(self, font=("Segoe UI", 18), bg="black", fg="white")
        self.text_label.place(
            x=20, y=1030, anchor="nw"
        )  # Note: Absolute positioning might need adjustment for screen size

        self.bind("<Configure>", self.on_resize)

        self.setup_keys()

        if self.files:
            self.display_image()
        else:
            self.text_label.configure(text="No images found in directory.")

    def on_resize(self, event):
        # Update text label position to be relative to bottom-left
        self.text_label.place(x=20, y=self.winfo_height() - 50, anchor="nw")

    def load_images(self):
        """Loads image files from the configured directory using pathlib."""
        if not self.image_path.exists():
            return []

        extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
        files = [f for f in self.image_path.iterdir() if f.is_file() and f.suffix.lower() in extensions]
        return sorted(files)

    def update_wait_time(self, value):
        step = 0.5 * value  # value is +1 or -1
        new_time = self.wait_time + step

        if 0 < new_time <= 30:
            self.wait_time = new_time
            self.config["delay"] = f"{self.wait_time:g}"
            ConfigManager.write(self.config)

            # Show feedback
            self.timer_info_label.place(relx=0.5, rely=0.5, anchor="center")
            self.timer_info_label.configure(text=f"{self.wait_time:g}s")

            # Cancel previous hide timer if it exists
            if self.info_timer_id:
                self.after_cancel(self.info_timer_id)

            # Hide after 1 second
            self.info_timer_id = self.after(1000, lambda: self.timer_info_label.place_forget())

    def display_image(self):
        if not self.files:
            return

        # Ensure index is within bounds
        self.current_image_index = self.current_image_index % len(self.files)
        self.change_image(self.files[self.current_image_index])

    def change_image(self, image_file: Path):
        try:
            # Open and resize image
            pil_image = Image.open(image_file)

            # Get screen dimensions
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # Calculate aspect ratios
            img_ratio = pil_image.width / pil_image.height
            screen_ratio = screen_width / screen_height

            if img_ratio > screen_ratio:
                # Image is wider than screen (relative to height) -> fit to width
                new_width = screen_width
                new_height = int(screen_width / img_ratio)
            else:
                # Image is taller than screen -> fit to height
                new_height = screen_height
                new_width = int(screen_height * img_ratio)

            # High-quality resize
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img = ImageTk.PhotoImage(pil_image)

            # Update the label
            self.image_label.configure(image=img)
            self.current_photo = img  # Keep reference to prevent garbage collection

            # Update status text
            self.text_label.configure(text=f"{self.current_image_index + 1}/{len(self.files)} {self.play_pause}")

        except Exception as e:
            print(f"Error loading image {image_file}: {e}")
            self.text_label.configure(text=f"Error loading image")

    def move(self, direction):
        if not self.files:
            return

        if direction == "right":
            self.current_image_index = (self.current_image_index + 1) % len(self.files)
        elif direction == "left":
            self.current_image_index = (self.current_image_index - 1) % len(self.files)

        self.change_image(self.files[self.current_image_index])

    def toggle_loop(self):
        if self.loop_active:
            self.stop_loop()
            self.play_pause = "⏸️"
        else:
            self.start_loop()
            self.play_pause = "▶️"

        if self.files:
            self.text_label.configure(text=f"{self.current_image_index + 1}/{len(self.files)} {self.play_pause}")

    def start_loop(self):
        if not self.loop_active:

            self.loop_active = True
        else:
            # If already active, this is a recursive call, so we move
            self.move("right")

        # Schedule next move
        delay_ms = int(self.wait_time * 1000)
        self.loop_id = self.after(delay_ms, self.start_loop)

    def stop_loop(self):
        self.loop_active = False
        if self.loop_id:
            self.after_cancel(self.loop_id)
            self.loop_id = None

    def delete_current_image(self, event=None):
        if not self.files:
            return

        current_file = self.files[self.current_image_index]

        # Create 'Trash' folder in the same directory as the images
        trash_dir = current_file.parent / "Trash"
        try:
            trash_dir.mkdir(exist_ok=True)

            # Move file to trash
            destination = trash_dir / current_file.name

            # Handle collision if file already exists in Trash
            if destination.exists():
                base = destination.stem
                suffix = destination.suffix
                counter = 1
                while destination.exists():
                    destination = trash_dir / f"{base}_{counter}{suffix}"
                    counter += 1

            shutil.move(str(current_file), str(destination))
            print(f"Moved to trash: {current_file} -> {destination}")

            # Remove from list
            del self.files[self.current_image_index]

            # Adjust index
            if self.current_image_index >= len(self.files):
                self.current_image_index = 0

            # Update display
            if self.files:
                self.change_image(self.files[self.current_image_index])
            else:
                self.image_label.configure(image="")
                self.text_label.configure(text="No images left.")

        except Exception as e:
            print(f"Error deleting file: {e}")

    def shuffle_images(self, event=None):
        if self.files:
            from random import shuffle
            shuffle(self.files)
            self.current_image_index = 0
            self.display_image()

    def setup_keys(self):
        keys = {
            "<Escape>": lambda event: self.destroy(),
            "<d>": lambda event: self.move("right"),
            "<Right>": lambda event: self.move("right"),
            "<a>": lambda event: self.move("left"),
            "<Left>": lambda event: self.move("left"),
            "<w>": lambda event: self.update_wait_time(1),
            "<Up>": lambda event: self.update_wait_time(1),
            "<s>": lambda event: self.update_wait_time(-1),
            "<Down>": lambda event: self.update_wait_time(-1),
            "<r>": self.shuffle_images,
            "<space>": lambda event: self.toggle_loop(),
            "<Shift-Delete>": self.delete_current_image,
        }
        for key, handler in keys.items():
            self.bind(key, handler)


class Settings(tk.Tk):
    def __init__(self):
        super().__init__()

        # Read cache
        self.config = ConfigManager.read()
        self.shuffled = tk.IntVar(value=int(self.config.get("shuffle", False)))

        # Do not load external theme - use default Tkinter theme
        self.title("Slide Show Settings")
        width = 740
        height = 260

        # Center window
        width_offset = self.winfo_screenwidth() // 2 - width // 2
        height_offset = self.winfo_screenheight() // 2 - height
        self.geometry(f"{width}x{height}+{width_offset}+{height_offset}")

        # Removed self.configure(background=bg) to use default system background
        self.resizable(False, False)

        # UI Layout
        style = ttk.Style()
        style.theme_use("clam")

        bg_color = "#2b2b2b"
        fg_color = "#ffffff"
        accent_color = "#0078d7"
        input_bg = "#1f1f1f"

        self.configure(background=bg_color)

        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 14))
        style.configure("TCheckbutton", background=bg_color, foreground=fg_color, font=("Segoe UI", 14))

        # Fix for Checkbutton indicator in clam theme
        style.map(
            "TCheckbutton",
            background=[("active", bg_color)],
            indicatorbackground=[("selected", accent_color), ("!selected", input_bg)],
            indicatorforeground=[("selected", "#ffffff")],
        )

        style.configure(
            "TEntry", fieldbackground=input_bg, foreground=fg_color, insertcolor=fg_color, borderwidth=1, relief="flat"
        )

        # Standard Button
        style.configure(
            "TButton",
            font=("Segoe UI", 14),
            background="#3a3a3a",
            foreground=fg_color,
            borderwidth=0,
            focuscolor=bg_color,
        )
        style.map("TButton", background=[("active", "#454545")])

        # Accent Button
        style.configure("Accent.TButton", font=("Segoe UI", 14, "bold"), background=accent_color, foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#0063b1")])

        self.frame0 = ttk.Frame(master=self)
        self.frame0.pack(expand=False, padx=15, pady=(10, 0), fill="x")
        self.frame0.grid_columnconfigure(0, weight=1)

        self.label0 = ttk.Label(master=self.frame0, text="Enter File Destination", font=("Segoe UI", 22))
        self.label0.grid(row=0, column=0, pady=(5, 0), columnspan=2)

        self.entry0 = ttk.Entry(master=self.frame0, font=("Segoe UI", 18))
        self.entry0.grid(row=1, column=0, padx=(5, 0), pady=5, ipady=3, sticky="WE")
        self.entry0.insert(0, self.config.get("path", ""))

        self.file_search_button = ttk.Button(master=self.frame0, command=self.open_file_explorer, text="📂", width=3)
        self.file_search_button.grid(row=1, column=1, padx=5, pady=5, ipady=5, sticky="W")

        self.frame1 = ttk.Frame(master=self)
        self.frame1.pack(expand=False, pady=10)

        self.label1 = ttk.Label(master=self.frame1, text="Enter wait time (s):", font=("Segoe UI", 18))
        self.label1.grid(row=0, column=0, ipady=5, padx=(5, 10), pady=3)

        self.entry1 = ttk.Entry(master=self.frame1, width=5, font=("Segoe UI", 18))
        self.entry1.grid(row=0, column=1, ipady=2, padx=(0, 5), pady=3)
        self.entry1.insert(0, str(self.config.get("delay", 2.5)))

        self.frame2 = ttk.Frame(master=self)
        self.frame2.pack(padx=20, pady=(5, 10), fill="x")

        # Use 'uniform' to force col 0 and 2 to have equal width, centering col 1
        self.frame2.grid_columnconfigure(0, weight=1, uniform="group1")
        self.frame2.grid_columnconfigure(1, weight=0)
        self.frame2.grid_columnconfigure(2, weight=1, uniform="group1")

        self.button = ttk.Button(master=self.frame2, style="Accent.TButton", text="Begin", command=self.begin, width=10)
        self.button.grid(row=0, column=1, ipady=5)

        self.checkbutton = ttk.Checkbutton(
            master=self.frame2, text="Randomize Order", variable=self.shuffled, offvalue=0, onvalue=1
        )
        self.checkbutton.grid(row=0, column=2, sticky="e")

        self.bind("<Return>", lambda event: self.begin())

    def open_file_explorer(self):
        initial_dir = self.config.get("path", ".")
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        filepath = filedialog.askdirectory(mustexist=True, initialdir=initial_dir)
        if filepath:
            self.entry0.delete(0, "end")
            self.entry0.insert(0, filepath)
            self.save_current_ui_to_config()

    def save_current_ui_to_config(self):
        self.config["path"] = self.entry0.get()
        self.config["delay"] = self.entry1.get()
        self.config["shuffle"] = bool(self.shuffled.get())
        ConfigManager.write(self.config)

    def begin(self):
        self.save_current_ui_to_config()
        self.destroy()
        app = App()
        app.mainloop()


if __name__ == "__main__":
    settings = Settings()
    settings.mainloop()
