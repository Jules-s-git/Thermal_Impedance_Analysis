# -*- coding: utf-8 -*-
"""Middle of the window: the plot tabs and the Notice tab."""

from .common import *  # noqa: F401,F403

NOTICE = [
    ("Foster Model",
     "The Foster model represents a thermal system as a series of parallel Rth_cauer branches. "
     "It is commonly used for system identification and allows easy reconstruction of thermal "
     "responses.", "Foster_model.png", (400, 200)),
    ("Cauer Model",
     "The Cauer model represents the system as a ladder of series Rth_cauer elements. It is "
     "useful for associating circuit elements with physical regions. The behavior described by "
     "the model is the basis for identifying the heat-flow path using structure functions.",
     "Cauer_model.png", (400, 200)),
    ("Cumulative Structure Function",
     "The cumulative structure function represents the accumulation of thermal capacitance "
     "versus thermal resistance. It helps identify layers of materials and heat storage in a "
     "system.", "cumulative_structure_function.png", (700, 300)),
    ("Differential Structure Function",
     "The differential structure function shows the rate of change of thermal capacitance with "
     "respect to resistance. Peaks in this function correspond to material interfaces or thermal "
     "barriers.", None, None),
]


class PlotsMixin:
    """Plot tabs. Uses the attributes of ThermalGUI."""

    def _add_toolbar(self, canvas, parent):
        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _add_plot_tab(self, notebook, title):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)
        fig, ax = plt.subplots(figsize=(6, 5))
        canvas = FigureCanvasTkAgg(fig, master=frame)
        self._add_toolbar(canvas, frame)
        return fig, ax, canvas

    def _build_plots_and_tables(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.notebook = notebook
        self.fig_Z, self.ax_Z, self.canvas_Z = self._add_plot_tab(notebook, "Zth")
        self.fig_dZ, self.ax_dZ, self.canvas_dZ = self._add_plot_tab(notebook, "dZ/dln(t)")
        self.fig_R, self.ax_R, self.canvas_R = self._add_plot_tab(notebook, "Spectrum R")
        self.fig_SF_cum, self.ax_SF_cum, self.canvas_SF_cum = self._add_plot_tab(
            notebook, "Structure (Cumulative)")
        self.fig_SF_diff, self.ax_SF_diff, self.canvas_SF_diff = self._add_plot_tab(
            notebook, "Structure (Differential)")

        table_frame = ttk.Frame(main)
        table_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
        self._build_notice(notebook)
        self._build_result_tables(table_frame)   # ResultsMixin

    def _build_notice(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Notice")
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._notice_photos = []  # keep references, or Tk drops the images
        for title, text, picture, size in NOTICE:
            ttk.Label(scroll_frame, text=title, font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 0))
            ttk.Label(scroll_frame, text=text, wraplength=1200, justify="left").pack(
                anchor="w", padx=10, pady=(0, 5) if picture else (0, 10))
            if picture:
                photo = ImageTk.PhotoImage(Image.open(ASSETS / picture).resize(size))
                self._notice_photos.append(photo)
                ttk.Label(scroll_frame, image=photo).pack(anchor="w", padx=10, pady=(0, 10))

    # ------------------------------------------------------------- plotting
    def _plot_all(self):
        ax = self.ax_Z
        ax.clear()
        ax.plot(self.time, self.Z_meas, label="Measured")
        ax.plot(self.time, self.Z_foster, "--", label="Foster")
        ax.set_xscale("log")
        ax.set_title("Thermal Impedance Zth")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("Zth")
        ax.grid(True)
        ax.legend()
        self.canvas_Z.draw()

        ax = self.ax_dZ
        ax.clear()
        ax.plot(self.z, self.dZ_dz, label="Measured")
        ax.plot(self.z_rec, self.dZ_rec, "--", label="Reconstructed")
        ax.set_title("Derivative of Zth with respect to ln(t)")
        ax.set_xlabel("ln(t)")
        ax.set_ylabel("dZ/dln(t)")
        ax.grid(True)
        ax.legend()
        self.canvas_dZ.draw()

        ax = self.ax_R
        ax.clear()
        ax.plot(self.z, self.R_spec, label="Measured spectrum")
        ax.plot(self.z_rec, self.R_rec, "--", label="Reconstructed spectrum")
        ax.set_title("Thermal Resistance Spectrum R(ln(t))")
        ax.set_xlabel("ln(t)")
        ax.set_ylabel("R(ln(t))")
        ax.grid(True)
        ax.legend()
        self.canvas_R.draw()

        # Cumulative structure function
        ax = self.ax_SF_cum
        ax.clear()
        ax.plot(self.Rth_cum, self.C_cum, marker="o", markersize=4, linestyle="--", linewidth=0.7)
        x_max = np.max(self.Rth_cum)
        ax.axvline(x=x_max, color="red", linestyle="-", linewidth=0.7)
        ax.set_yscale("log")
        ymin_cum = 10 ** np.floor(np.log10(self.C_cum.min()))
        ymax = self.C_cum[-1]
        for i in range(len(self.Rth_cum)):
            if self.Rth_cum[i] > 0.993 * self.Rth_cum.max():
                ymax = self.C_cum[i]
                break
        ax.set_ylim(bottom=ymin_cum, top=ymax)
        ax.text(x_max, ax.get_ylim()[0], f"{x_max:.3f}", color="red", fontsize=10,
                ha="right", va="bottom")
        ax.set_xlim(left=0, right=x_max * 1.1)
        ax.set_xlabel("Cumulative thermal resistance RΣ [K/W]")
        ax.set_ylabel("Cumulative thermal capacitance CΣ [J/K]")
        ax.set_title("Cumulative structure function")
        ax.grid(True, which="both")
        self.canvas_SF_cum.draw()

        # Differential structure function
        ax = self.ax_SF_diff
        ax.clear()
        ax.plot(self.Rth_diff, self.dC_dRth, marker="o", markersize=4, linestyle="--", linewidth=0.7)
        ax.axvline(x=x_max, color="red", linestyle="-", linewidth=0.7)
        ax.set_yscale("log")
        ymin_diff = 10 ** np.floor(np.log10(self.dC_dRth.min()))
        ax.set_ylim(bottom=ymin_diff, top=(ymin_diff / ymin_cum) * ymax)
        ax.text(x_max, ax.get_ylim()[0], f"{x_max:.3f}", color="red", fontsize=10,
                ha="right", va="bottom")
        ax.set_xlim(left=0, right=x_max * 1.1)
        ax.set_xlabel("Rth [K/W]")
        ax.set_ylabel(f"dCΣ / dRΣ [{config.DIFFERENTIAL_UNIT_LABEL}]")
        ax.set_title("Differential structure function")
        ax.grid(True, which="both")
        self.canvas_SF_diff.draw()
