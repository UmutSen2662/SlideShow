import tkinter.ttk as ttk
import tkinter as tk
import json, os
from PIL import Image, ImageTk
from tkinter import filedialog
from threading import Timer
from random import shuffle
from glob import glob


def resource_path(relative_path):
    base_path = os.getcwd()
    return os.path.join(base_path, relative_path)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Read cache and initialize variables
        data = self.read_cache()
        self.shuffled = data["shuffle"]
        self.wait_time = float(data["delay"])

        self.current_image_index = 0
        self.loop_active = False
        self.loop_timer = None
        self.play_pause = "⏸️"

        # Get a list of the image files in the folder
        self.files = glob(data["path"] + "/*.jpg") + glob(data["path"] + "/*.png")

        # Create the main window
        self.configure(bg="black")
        self.attributes("-fullscreen", True)
        self.focus_force()

        # Create a label to display the image
        self.image_label = tk.Label(self, bg="black")
        self.image_label.pack()

        # Create a label to display the text
        self.text_label = tk.Label(self, font=(None, 18), bg="black", fg="white")
        self.text_label.place(x=20, y=1030, anchor="nw")

        # Setup key binding and display the first image
        self.setup_keys()
        self.display_image()

    def read_cache(self):
        if os.path.exists("cache.json"):
            with open("cache.json", "r") as file:
                data = json.load(file)
            return data

    def display_image(self):
        if self.shuffled == True:
            shuffle(self.files)
        self.current_image_index = 0
        self.change_image(self.files[self.current_image_index])

    def change_image(self, image_file):
        # Convert the image to a PhotoImage object
        img = ImageTk.PhotoImage(Image.open(image_file))

        # Update the label to display the new image
        self.image_label.configure(image=img)
        self.image_label.image = img

        # Update the text label to display the current image index
        self.text_label.configure(text=str(self.current_image_index + 1) + self.play_pause)

    def move(self, direction):
        if direction == "right":
            if self.current_image_index == len(self.files) - 1:
                self.current_image_index = 0
            else:
                self.current_image_index += 1
        elif direction == "left":
            if self.current_image_index == 0:
                self.current_image_index = len(self.files) - 1
            else:
                self.current_image_index -= 1
        self.change_image(self.files[self.current_image_index])

    def toggle_loop(self):
        if self.loop_active:
            self.stop_loop()
            self.play_pause = "⏸️"
            self.text_label.configure(text=str(self.current_image_index + 1) + self.play_pause)
        else:
            self.start_loop()
            self.play_pause = "▶️"
            self.text_label.configure(text=str(self.current_image_index + 1) + self.play_pause)

    def start_loop(self):
        # Starts the loop
        if self.loop_active:
            self.move("right")
        self.loop_active = True
        self.loop_timer = Timer(self.wait_time, self.start_loop)
        self.loop_timer.start()

    def stop_loop(self):
        # Stops the loop
        self.loop_active = False
        if self.loop_timer is not None:
            self.loop_timer.cancel()

    def delete(self, event):
        os.remove(self.files[self.current_image_index])
        del self.files[self.current_image_index]
        self.current_image_index -= 1
        self.move("right")

    def setup_keys(self):
        # Key bindings
        keys = {
            "<Escape>": lambda event: self.destroy(),
            "<d>": lambda event: self.move("right"),
            "<a>": lambda event: self.move("left"),
            "<Right>": lambda event: self.move("right"),
            "<Left>": lambda event: self.move("left"),
            "<r>": lambda event: self.display_image(),
            "<space>": lambda event: self.toggle_loop(),
            "<Shift-Delete>": self.delete,
        }
        for key, handler in keys.items():
            self.bind(key, handler)


class Settings(tk.Tk):
    def __init__(self):
        super().__init__()

        # Read cache
        self.data = self.read_cache()
        self.shuffled = tk.IntVar(value=self.data["shuffle"])

        self.tk.call("source", resource_path(r"Azure\azure.tcl"))
        self.tk.call("set_theme", "dark")

        bg = "#404040"
        self.title("Slide Show Settings")
        width = 740
        height = 230
        width_offset = self.winfo_screenwidth() // 2 - width // 2
        height_offset = self.winfo_screenheight() // 2 - height
        self.geometry(f"{width}x{height}+{width_offset}+{height_offset}")
        self.configure(background=bg)
        self.resizable(False, False)

        style = ttk.Style()
        style.configure("TButton", font=(None, 14))
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground="white")
        style.configure("TCheckbutton", background=bg, font=(None, 14))

        self.frame0 = ttk.Frame(master=self, width=20)
        self.frame0.pack(expand=False, padx=15, pady=(10, 0), fill="x")

        self.frame0.grid_columnconfigure((0), weight=1)
        self.frame0.grid_rowconfigure((0, 1), weight=1)

        self.label0 = ttk.Label(master=self.frame0, text="Enter File Destination", font=(None, 22))
        self.label0.grid(row=0, column=0, pady=(5, 0), columnspan=2)

        self.entry0 = ttk.Entry(master=self.frame0, font=(None, 18))
        self.entry0.grid(row=1, column=0, padx=(5, 0), pady=5, ipady=3, sticky="WE")
        self.entry0.insert(0, self.data["path"])

        self.file_search_button = ttk.Button(master=self.frame0, command=self.open_file_explorer, text="📂", width=2)
        self.file_search_button.grid(row=1, column=1, padx=5, pady=5, ipady=5, sticky="W")

        self.frame1 = ttk.Frame(master=self, width=20)
        self.frame1.pack(expand=False)

        self.label1 = ttk.Label(master=self.frame1, text="Enter wait time:", font=(None, 18))
        self.label1.grid(row=0, column=0, ipady=5, padx=(5, 0), pady=3)

        self.entry1 = ttk.Entry(master=self.frame1, width="3", font=(None, 18))
        self.entry1.grid(row=0, column=1, ipady=2, padx=(0, 5), pady=3)
        self.entry1.insert(0, self.data["delay"])

        self.frame2 = ttk.Frame(master=self, width=500)
        self.frame2.pack(padx=20, pady=(5, 10), fill="x")
        self.frame2.grid_columnconfigure((0, 2), weight=1)

        self.empty = ttk.Label(master=self.frame2, width=14)
        self.empty.grid(row=0, column=0)

        self.button = ttk.Button(master=self.frame2, style="Accent.TButton", text="Begin", command=self.begin, width=6)
        self.button.grid(ipady=3, row=0, column=1)

        self.checkbutton = ttk.Checkbutton(
            master=self.frame2, text="Randomize", variable=self.shuffled, offvalue=0, onvalue=1
        )
        self.checkbutton.grid(row=0, column=2, sticky="e")

        self.bind("<Return>", lambda event: self.begin())

    def read_cache(self):
        if os.path.exists("cache.json"):
            with open("cache.json", "r") as file:
                data = json.load(file)
            return data
        else:
            path = ""
            delay = 0
            shuffle = False
            data = {"path": path, "delay": delay, "shuffle": shuffle}
            with open("cache.json", "w") as file:
                json.dump(data, file)
            return data

    def open_file_explorer(self):
        filepath = filedialog.askdirectory(mustexist=True, initialdir=self.data["path"])
        if filepath != "":
            self.entry0.delete(0, "end")
            self.entry0.insert(0, filepath)
            self.write_cache()

    def write_cache(self):
        if os.path.exists("cache.json"):
            with open("cache.json", "w") as file:
                self.data["path"] = self.entry0.get()
                self.data["delay"] = self.entry1.get()
                self.data["shuffle"] = bool(self.shuffled.get())
                json.dump(self.data, file)

    def begin(self):
        self.write_cache()
        self.destroy()
        app = App()
        app.mainloop()


settings = Settings()
settings.mainloop()
