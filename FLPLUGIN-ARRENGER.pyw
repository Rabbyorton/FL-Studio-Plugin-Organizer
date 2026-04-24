import os
import shutil
import configparser
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

PROHIBITED_FOLDER_NAME_CHARS = ':/\\"*|?<>'  # invalid in Windows folder names

# Set the modern Flutter/Fluent aesthetic
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class FLOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FL Studio Plugin Organizer")
        self.geometry("850x650")
        self.minsize(850, 650)

        # Grid layout configuration
        # 0: header, 1: config, 2: stats, 3: log
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Default Paths
        default_db = (
            Path.home()
            / "Documents"
            / "Image-Line"
            / "FL Studio"
            / "Presets"
            / "Plugin database"
            / "Installed"
        )
        default_out = Path.home() / "Desktop" / "Organized_FL_Plugins"

        self.source_path = ctk.StringVar(value=str(default_db))
        self.dest_path = ctk.StringVar(value=str(default_out))

        # Stats variables
        self.scanned_count = ctk.IntVar(value=0)
        self.copied_count = ctk.IntVar(value=0)
        self.skipped_count = ctk.IntVar(value=0)
        self.error_count = ctk.IntVar(value=0)

        self.setup_ui()

    def setup_ui(self):
        # --- HEADER SECTION (title + top actions) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        # Left: title + subtitle
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="FL Studio Plugin Organizer",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Organize FL Studio plugin presets by vendor in one click.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="gray",
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w")

        # Right: top-level actions
        self.header_actions = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.header_actions.grid(row=0, column=1, rowspan=2, padx=(10, 0), sticky="e")

        self.btn_organize = ctk.CTkButton(
            self.header_actions,
            text="Organize Plugins",
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_organizer_thread,
        )
        self.btn_organize.pack(side="left", padx=(0, 8))

        self.btn_open = ctk.CTkButton(
            self.header_actions,
            text="Open Folder",
            height=34,
            fg_color="#3f3f46",
            hover_color="#52525b",
            font=ctk.CTkFont(size=13),
            state="disabled",
            command=self.open_output,
        )
        self.btn_open.pack(side="left")

        # --- PATH CONFIGURATION CARD ---
        self.config_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#18181b")
        self.config_frame.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")
        self.config_frame.grid_columnconfigure(1, weight=1)

        # Source Input
        self.lbl_source = ctk.CTkLabel(
            self.config_frame,
            text="Source Path",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#d4d4d8",
        )
        self.lbl_source.grid(row=0, column=0, padx=16, pady=(16, 6), sticky="w")

        self.entry_source = ctk.CTkEntry(
            self.config_frame,
            textvariable=self.source_path,
            height=32,
            corner_radius=8,
            fg_color="#27272a",
            border_color="#3f3f46",
        )
        self.entry_source.grid(row=0, column=1, padx=(0, 8), pady=(16, 6), sticky="ew")

        self.btn_browse_source = ctk.CTkButton(
            self.config_frame,
            text="Browse",
            width=90,
            height=32,
            fg_color="#3f3f46",
            hover_color="#52525b",
            font=ctk.CTkFont(size=12),
            command=lambda: self.browse(self.source_path),
        )
        self.btn_browse_source.grid(row=0, column=2, padx=(0, 16), pady=(16, 6))

        # Output Input
        self.lbl_dest = ctk.CTkLabel(
            self.config_frame,
            text="Output Path",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#d4d4d8",
        )
        self.lbl_dest.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")

        self.entry_dest = ctk.CTkEntry(
            self.config_frame,
            textvariable=self.dest_path,
            height=32,
            corner_radius=8,
            fg_color="#27272a",
            border_color="#3f3f46",
        )
        self.entry_dest.grid(row=1, column=1, padx=(0, 8), pady=(0, 16), sticky="ew")

        self.btn_browse_dest = ctk.CTkButton(
            self.config_frame,
            text="Browse",
            width=90,
            height=32,
            fg_color="#3f3f46",
            hover_color="#52525b",
            font=ctk.CTkFont(size=12),
            command=lambda: self.browse(self.dest_path),
        )
        self.btn_browse_dest.grid(row=1, column=2, padx=(0, 16), pady=(0, 16))

        # --- COMPACT STATS PANEL ---
        self.stats_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#111827")
        self.stats_frame.grid(row=2, column=0, padx=20, pady=(0, 8), sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def make_stat_card(parent, col, label_text, var, color):
            card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#020617")
            card.grid(row=0, column=col, padx=6, pady=6, sticky="nsew")

            title = ctk.CTkLabel(
                card,
                text=label_text,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#9ca3af",
            )
            title.pack(anchor="w", padx=10, pady=(6, 0))

            value = ctk.CTkLabel(
                card,
                textvariable=var,
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                text_color=color,
            )
            value.pack(anchor="w", padx=10, pady=(0, 8))

        make_stat_card(self.stats_frame, 0, "Scanned", self.scanned_count, "#38bdf8")
        make_stat_card(self.stats_frame, 1, "Copied", self.copied_count, "#22c55e")
        make_stat_card(self.stats_frame, 2, "Skipped", self.skipped_count, "#eab308")
        make_stat_card(self.stats_frame, 3, "Errors", self.error_count, "#f97316")

        # --- LOG CONSOLE (fills remaining space) ---
        self.log_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#18181b")
        self.log_frame.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.lbl_log = ctk.CTkLabel(
            self.log_frame,
            text="Activity Console",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        self.lbl_log.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        # Progress bar inside log frame header area to save vertical space
        self.progress = ctk.CTkProgressBar(
            self.log_frame,
            mode="indeterminate",
            width=220,
        )
        self.progress.grid(row=0, column=1, padx=16, pady=(12, 4), sticky="e")
        self.progress.set(0)
        self.progress.grid_remove()  # hidden initially

        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#4ade80",
            fg_color="#020617",
            corner_radius=8,
        )
        self.log_text.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="nsew")
        self.log_text.configure(state="disabled")

    def browse(self, string_var):
        folder = filedialog.askdirectory(initialdir=string_var.get())
        if folder:
            string_var.set(folder)

    def log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def start_organizer_thread(self):
        # Disable buttons and start progress animation
        self.btn_organize.configure(state="disabled")
        self.btn_open.configure(state="disabled")
        self.progress.grid()  # show progress bar
        self.progress.start()

        # Clear console
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        # Reset stats
        self.scanned_count.set(0)
        self.copied_count.set(0)
        self.skipped_count.set(0)
        self.error_count.set(0)

        # Run process in background thread so UI doesn't freeze
        threading.Thread(target=self.run_organizer, daemon=True).start()

    def run_organizer(self):
        source = Path(self.source_path.get())
        output = Path(self.dest_path.get())

        if not source.is_dir():
            self.after(
                0,
                lambda: messagebox.showerror(
                    "Error", "Source directory does not exist."
                ),
            )
            self.after(0, self.reset_ui)
            return

        self.after(0, lambda: self.log("Starting organization process..."))

        effects_out = output / "Effects"
        generators_out = output / "Generators"

        try:
            effects_out.mkdir(parents=True, exist_ok=True)
            generators_out.mkdir(parents=True, exist_ok=True)
            self.after(
                0,
                lambda: self.log(f"Created output directories at {output}"),
            )
        except Exception as e:
            self.after(
                0,
                lambda err=e: self.log(f"Error creating output dirs: {err}"),
            )
            self.after(0, self.reset_ui)
            return

        subfolders = [
            ("Effects", source / "Effects" / "VST"),
            ("Effects", source / "Effects" / "VST3"),
            ("Generators", source / "Generators" / "VST"),
            ("Generators", source / "Generators" / "VST3"),
        ]

        config_parser = configparser.ConfigParser()
        total_copied = 0
        total_scanned = 0
        total_skipped = 0
        total_errors = 0

        for category, folder in subfolders:
            if not folder.is_dir():
                self.after(
                    0,
                    lambda c=category, f=folder: self.log(
                        f"Skipping {f.name} (Not found)"
                    ),
                )
                continue

            self.after(0, lambda f=folder: self.log(f"\nScanning {f.name}..."))

            for nfo_file in folder.glob("*.nfo"):
                total_scanned += 1
                self.after(0, lambda v=total_scanned: self.scanned_count.set(v))

                try:
                    with open(
                        nfo_file, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        stream = f.read()

                    config_string = "[dummy_section]\n" + stream
                    config_parser.read_string(config_string)

                    vendor = config_parser["dummy_section"].get(
                        "ps_file_vendorname_0", "Unknown_Vendor"
                    )

                    for char in PROHIBITED_FOLDER_NAME_CHARS:
                        vendor = vendor.replace(char, "")
                    vendor = vendor.strip() or "Unknown_Vendor"

                    target_base = (
                        generators_out if category == "Generators" else effects_out
                    )
                    vendor_dir = target_base / vendor
                    vendor_dir.mkdir(exist_ok=True)

                    fst_file = nfo_file.with_suffix(".fst")
                    png_file = nfo_file.with_suffix(".png")

                    if fst_file.is_file():
                        shutil.copy2(fst_file, vendor_dir)
                        shutil.copy2(nfo_file, vendor_dir)
                        if png_file.is_file():
                            shutil.copy2(png_file, vendor_dir)

                        total_copied += 1
                        self.after(0, lambda v=total_copied: self.copied_count.set(v))
                        self.after(
                            0,
                            lambda stem=fst_file.stem, cat=category, ven=vendor: self.log(
                                f"Copied: {stem} -> {cat}/{ven}"
                            ),
                        )
                    else:
                        total_skipped += 1
                        self.after(0, lambda v=total_skipped: self.skipped_count.set(v))
                        self.after(
                            0,
                            lambda name=nfo_file.name: self.log(
                                f"Skipped (no .fst found for {name})"
                            ),
                        )

                except Exception as e:
                    total_errors += 1
                    self.after(0, lambda v=total_errors: self.error_count.set(v))
                    self.after(
                        0,
                        lambda name=nfo_file.name, err=e: self.log(
                            f"Error reading {name}: {err}"
                        ),
                    )

        self.after(
            0,
            lambda: self.log(
                f"\nDone. Scanned: {total_scanned}, Copied: {total_copied}, "
                f"Skipped: {total_skipped}, Errors: {total_errors}"
            ),
        )
        self.after(0, lambda: self.finish_success(total_copied))

    def finish_success(self, total: int):
        self.reset_ui()
        self.btn_open.configure(state="normal")
        messagebox.showinfo(
            "Complete",
            f"Finished organizing {total} plugins.\nCheck your output folder.",
        )

    def reset_ui(self):
        self.progress.stop()
        self.progress.grid_remove()
        self.btn_organize.configure(state="normal")

    def open_output(self):
        output = Path(self.dest_path.get())
        if output.exists():
            os.startfile(output)


if __name__ == "__main__":
    app = FLOrganizerApp()
    app.mainloop()