from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from types import SimpleNamespace

from convert_strava_timestamp import resolve_target_start, shift_gpx_timestamps


def convert(input_path: Path, date: str, clock: str, offset: int) -> tuple[Path, datetime]:
    hour, minute = (int(part) for part in clock.lower().replace("h", ":").split(":"))
    target = resolve_target_start(
        SimpleNamespace(date=date or None, hour=hour, minute=minute, timezone_offset=offset)
    )
    output_path = input_path.with_name(
        f"{input_path.stem}_{target:%Y%m%d}_{hour:02d}{minute:02d}_gmt{offset}{input_path.suffix}"
    )
    shift_gpx_timestamps(input_path, output_path, target)
    return output_path, target


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Strava GPX time shifter")
        self.resizable(False, False)

        self.file = tk.StringVar()
        self.date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.clock = tk.StringVar(value="18:00")
        self.offset = tk.StringVar(value="7")

        frame = ttk.Frame(self, padding=12)
        frame.grid()
        ttk.Button(frame, text="Upload GPX file...", command=self.pick_file).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.file, width=50).grid(row=0, column=1, columnspan=3, sticky="w", padx=8)

        for row, (label, var) in enumerate(
            [("Date (YYYY-MM-DD)", self.date), ("Start time (HH:MM)", self.clock), ("Timezone GMT+", self.offset)],
            start=1,
        ):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(frame, textvariable=var, width=14).grid(row=row, column=1, sticky="w", padx=8)

        ttk.Button(frame, text="Convert", command=self.run).grid(row=4, column=0, pady=(8, 0), sticky="w")

    def pick_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("GPX files", "*.gpx"), ("All files", "*.*")])
        if path:
            self.file.set(path)

    def run(self) -> None:
        if not self.file.get():
            messagebox.showerror("Error", "Upload a GPX file first.")
            return
        try:
            output_path, target = convert(
                Path(self.file.get()), self.date.get().strip(), self.clock.get().strip(), int(self.offset.get())
            )
        except Exception as error:
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Done", f"Start set to {target:%Y-%m-%d %H:%M} (GMT{target:%z})\n\nSaved:\n{output_path}")


if __name__ == "__main__":
    App().mainloop()
