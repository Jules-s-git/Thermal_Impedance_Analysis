# -*- coding: utf-8 -*-
"""Results: editable Foster table, result tables, copy and export."""

from .common import *  # noqa: F401,F403

TEXT_WIDTH, TEXT_HEIGHT = 30, 10


class ResultsMixin:
    """Result tables and exports. Uses the attributes of ThermalGUI."""

    # ------------------------------------------------- editable Foster table
    def _build_foster_editor(self, frame):
        ttk.Label(frame, text="Edit Foster Poles").pack(anchor="w", pady=(15, 0))
        self.foster_table = ttk.Treeview(frame, columns=("Rth_foster", "tau_foster"),
                                         show="headings", height=8)
        for col in ("Rth_foster", "tau_foster"):
            self.foster_table.heading(col, text=col)
            self.foster_table.column(col, width=100)
        self.foster_table.pack(anchor="w")

        buttons = ttk.Frame(frame)
        buttons.pack(anchor="w", pady=5)
        ttk.Button(buttons, text="Add Pole", command=self._add_foster_pole).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons, text="Update Foster Model",
                   command=self._update_foster_from_table).pack(side=tk.LEFT, padx=5)

        self.foster_table.tag_configure("modified", foreground=ORANGE)
        self.foster_table.bind("<Double-1>", self._edit_foster_cell)

    def _add_foster_pole(self):
        self.foster_table.insert("", "end", values=(0.0, 0.0), tags=("modified",))

    def _edit_foster_cell(self, event):
        item = self.foster_table.identify_row(event.y)
        column = self.foster_table.identify_column(event.x)
        if not item or not column:
            return
        x, y, width, height = self.foster_table.bbox(item, column)
        entry = tk.Entry(self.foster_table)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, self.foster_table.set(item, column))
        entry.focus()

        def save_edit(event):
            self.foster_table.set(item, column, entry.get())
            if "modified" not in self.foster_table.item(item, "tags"):
                self.foster_table.item(item, tags=("modified",))
            entry.destroy()

        entry.bind("<KeyRelease>", lambda e: self.foster_table.set(item, column, entry.get()))
        entry.bind("<FocusOut>", save_edit)

    def _update_foster_from_table(self):
        try:
            rows = [self.foster_table.item(row)["values"] for row in self.foster_table.get_children()]
            self.Rth_foster = np.array([float(v[0]) for v in rows])
            self.tau_foster = np.array([float(v[1]) for v in rows])
            self.Z_foster = reconstruct_foster(self.time, self.Rth_foster, self.tau_foster)
            self._plot_all()
            self.status.config(text="Foster model updated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --------------------------------------------------------- result tables
    def _build_result_tables(self, table_frame):
        results = ttk.Frame(table_frame)
        results.pack(padx=5, pady=5, fill=tk.Y)
        for name, attr, copy in [
            ("Foster (Rth_foster, tau_foster)", "foster_text", self._copy_foster),
            ("Cauer (Rth_cauer, C_cauer)", "cauer_text", self._copy_cauer),
            ("Cumulative SF (RΣ, CΣ)", "sf_cum_text", self._copy_sf_cum),
            ("Differential SF (RΣ, dC/dR)", "sf_diff_text", self._copy_sf_diff),
        ]:
            frame = ttk.Frame(results, width=TEXT_WIDTH * 8, height=TEXT_HEIGHT * 18)
            frame.pack_propagate(False)
            frame.pack(padx=5, pady=5)
            ttk.Label(frame, text=name).pack()
            ttk.Button(frame, text="Copy", command=copy).pack(pady=2)
            text = tk.Text(frame, width=TEXT_WIDTH, height=TEXT_HEIGHT)
            text.pack(pady=5, fill=tk.BOTH, expand=True)
            setattr(self, attr, text)

    @staticmethod
    def _set_text(widget, a, b):
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, data_io.two_columns(a, b))

    def _update_gui_outputs(self):
        self._set_text(self.sf_cum_text, self.Rth_cum, self.C_cum)
        self._set_text(self.sf_diff_text, self.Rth_diff, self.dC_dRth)
        self._plot_all()
        self._fill_tables()

    def _fill_tables(self):
        self._set_text(self.foster_text, self.Rth_foster, self.tau_foster)
        self._set_text(self.cauer_text, self.Rth_cauer, self.C_cauer)
        for row in self.foster_table.get_children():
            self.foster_table.delete(row)
        for R, t in zip(self.Rth_foster, self.tau_foster):
            self.foster_table.insert("", "end", values=(f"{R:.6g}", f"{t:.6g}"))

    # ------------------------------------------------------------------ copy
    def _to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def _copy_foster(self):
        self._to_clipboard(self.foster_text.get("1.0", tk.END))

    def _copy_cauer(self):
        self._to_clipboard(self.cauer_text.get("1.0", tk.END))

    def _copy_sf_cum(self):
        self._to_clipboard(data_io.two_columns(self.Rth_cum, self.C_cum))

    def _copy_sf_diff(self):
        self._to_clipboard(data_io.two_columns(self.Rth_diff, self.dC_dRth))

    def _copy_all_data(self):
        table = data_io.results_table(self, diff_name="dC_dR")
        self._to_clipboard(table.to_csv(index=False, sep="\t"))

    # ---------------------------------------------------------------- export
    def _export_all_data(self):
        """Excel workbook (one sheet per table) or CSV file, after the extension."""
        types = [("Excel workbook", "*.xlsx"), ("CSV files", "*.csv")]
        if not config.EXCEL_EXPORT:  # switch N2: CSV first, as Zth_to_Foster
            types.reverse()
        try:
            file = filedialog.asksaveasfilename(defaultextension=types[0][1][1:], filetypes=types)
            if not file:
                return
            if file.lower().endswith(".csv"):
                data_io.results_table(self, diff_name="dC/dR").to_csv(file, index=False)
            else:
                data_io.export_excel(self, file, diff_unit=config.DIFFERENTIAL_UNIT_LABEL)
            self.status.config(text=f"Data exported: {os.path.basename(file)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_pdf(self):
        try:
            filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not filename:
                return
            data_io.export_pdf(self, filename, diff_unit=config.DIFFERENTIAL_UNIT_LABEL)
            self.status.config(text=f"PDF exported: {filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_ltspice(self):
        """LTspice models (Foster and Cauer) of the network of the table, edits included."""
        try:
            if len(getattr(self, "Rth_foster", [])) == 0:
                messagebox.showerror("Error", "Process data first: there is no Foster network to export.")
                return
            folder = filedialog.askdirectory(title="Folder for the LTspice models")
            if not folder:
                return
            time = getattr(self, "time", None)
            model = ltspice.write_ltspice(self.Rth_foster, self.tau_foster, folder,
                                          t_end=time[-1] if time is not None and len(time) else None,
                                          source=getattr(self, "current_file", None))
            self.status.config(text="LTspice models exported: " + ", ".join(model.names))
            if model.notes:
                messagebox.showwarning("LTspice", "\n".join(model.notes))
        except Exception as e:
            messagebox.showerror("Error", str(e))

