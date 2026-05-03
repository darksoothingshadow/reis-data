import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.course import GradeDistribution

GRADE_KEYS = GradeDistribution.GRADE_KEYS
BAR_COLORS = ["#4CAF50", "#8BC34A", "#CDDC39", "#FFC107", "#FF9800", "#f44336", "#9C27B0"]


class GradeChart:
    """Matplotlib bar chart embedded in a tkinter parent widget."""

    def __init__(self, parent):
        self._fig = Figure(figsize=(6, 3.2), dpi=96, facecolor="#222222")
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._fig, master=parent)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._draw_empty()

    def update(self, distributions: list[GradeDistribution]) -> None:
        self._ax.clear()
        if not distributions:
            self._draw_empty()
            return

        n_semesters = len(distributions)
        x = np.arange(len(GRADE_KEYS))
        width = 0.8 / n_semesters

        for i, dist in enumerate(distributions):
            counts = [dist.grades[g] for g in GRADE_KEYS]
            offset = (i - n_semesters / 2 + 0.5) * width
            bars = self._ax.bar(x + offset, counts, width, label=dist.semester_name)
            for bar in bars:
                bar.set_alpha(0.85)

        self._ax.set_xticks(x)
        self._ax.set_xticklabels(GRADE_KEYS, color="white")
        self._ax.tick_params(colors="white")
        self._ax.set_facecolor("#2b2b2b")
        self._ax.spines[:].set_color("#555555")
        self._ax.yaxis.label.set_color("white")
        self._ax.legend(
            fontsize=7, facecolor="#333333", labelcolor="white", framealpha=0.7
        )
        self._fig.tight_layout()
        self._canvas.draw()

    def clear(self) -> None:
        self._ax.clear()
        self._draw_empty()

    def _draw_empty(self) -> None:
        self._ax.set_facecolor("#2b2b2b")
        self._ax.text(
            0.5, 0.5, "Vyberte předmět",
            transform=self._ax.transAxes,
            ha="center", va="center", color="#888888", fontsize=12,
        )
        self._ax.tick_params(colors="#555555")
        self._ax.spines[:].set_color("#555555")
        self._fig.tight_layout()
        self._canvas.draw()
