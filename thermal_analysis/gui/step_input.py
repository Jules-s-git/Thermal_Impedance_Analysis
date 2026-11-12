# -*- coding: utf-8 -*-
"""Left panel of the window: data box, Load File, Process, status lines."""

from .common import *  # noqa: F401,F403


class InputMixin:
    """Data input and processing. Uses the attributes of ThermalGUI."""

    def _build_controls(self):
        frame = ttk.Frame(self.root)
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Data input
        ttk.Label(frame, text="Paste your data (time, Zth)").pack(anchor="w")
        self.data_frame = tk.Frame(frame, highlightthickness=0)
        self.data_frame.pack(anchor="w")
        self.data_text = scrolledtext.ScrolledText(self.data_frame, width=30, height=20, borderwidth=0)
        self.data_text.pack()
        self.data_text.bind("<<Modified>>", self._on_text_modified)

        # Maximum number of Foster branches
        ttk.Label(frame, text="Maximum number of Foster branches").pack(anchor="w", pady=(5, 0))
        self.branches_entry = ttk.Entry(frame, width=10)
        self.branches_entry.insert(0, str(config.DEFAULT_MAX_BRANCHES))
        self.branches_entry.pack(anchor="w")

        # Load and process
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="w", pady=10)
        ttk.Button(buttons, text="Load File", command=self._load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons, text="Process", command=self._process_data).pack(side=tk.LEFT, padx=5)

        # Copy and export
        exports = ttk.Frame(frame)
        exports.pack(anchor="w", pady=5)
        ttk.Button(exports, text="Copy All Data", command=self._copy_all_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(exports, text="Export All Data", command=self._export_all_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(exports, text="Export PDF", command=self._export_pdf).pack(side=tk.LEFT, padx=5)
        exports2 = ttk.Frame(frame)
        exports2.pack(anchor="w", pady=(0, 5))
        ttk.Button(exports2, text="Export LTspice", command=self._export_ltspice).pack(side=tk.LEFT, padx=5)

        # Editable Foster table (ResultsMixin)
        self._build_foster_editor(frame)

        ttk.Label(frame, text="").pack(pady=10)

        # Status lines
        self.current_file_status = ttk.Label(frame, text="File: None", foreground="blue")
        self.current_file_status.pack(anchor="w", pady=5)
        self.status = ttk.Label(frame, text="", foreground="blue")
        self.status.pack(anchor="w", pady=5)

    # ----------------------------------------------------------------- input
    def _load_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv"), ("Text", "*.txt")])
        if not filename:
            return
        try:
            times, values = data_io.read_for_window(filename)
            self.data_text.delete("1.0", tk.END)
            self.data_text.insert(tk.END, "time\tZth\n")
            for t, z in zip(times, values):
                self.data_text.insert(tk.END, f"{t}\t{z}\n")
            self._mark_unprocessed()
            self.file_loaded = True
            self.file_processed = False
            self.current_file = os.path.basename(filename)
            self.current_file_status.config(text=f"File: {self.current_file}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _mark_unprocessed(self):
        self.data_frame.config(highlightthickness=2, highlightbackground=ORANGE, highlightcolor=ORANGE)

    def _on_text_modified(self, event):
        self.data_text.edit_modified(False)  # prevents an infinite modification loop
        if self.file_processed:
            self._mark_unprocessed()
            self.file_processed = False

    def _parse_input_data(self):
        self.time, self.Z_meas = data_io.parse_text(self.data_text.get("1.0", tk.END))
        self.n_branches = int(self.branches_entry.get())

    # ------------------------------------------------------------ processing
    def _set_status(self, text):
        self.status.config(text=text)
        self.root.update()

    def _process_data(self):
        try:
            self._parse_input_data()
            res = analyse(self.time, self.Z_meas, self.n_branches, structure="pyrth",
                          spectra=True, progress=self._set_status)
            for name in ("z", "dZ_dz", "M_opt", "Rth_foster", "tau_foster", "C_foster", "Z_foster",
                         "z_rec", "dZ_rec", "R_spec", "R_rec", "Rth_cauer", "C_cauer",
                         "Rth_cum", "C_cum", "Rth_diff", "dC_dRth"):
                setattr(self, name, getattr(res, name))
            self.result = res
            self._update_gui_outputs()
            self.status.config(text="Processed successfully")
            self.data_frame.config(highlightthickness=0)
            self.file_processed = True
        except Exception as e:
            messagebox.showerror("Error", str(e))
