import numpy as np
import matplotlib
import matplotlib.ticker
# Backend must be set before importing Figure/FigureCanvasTkAgg.
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.course import GradeDistribution

# One colour per semester bar group (cycles if more than 7 semesters shown).
BAR_COLORS = ["#4CAF50", "#FFC107", "#2196F3", "#FF9800", "#9C27B0", "#f44336", "#00BCD4"]


class GradeChart:
    """Matplotlib bar chart embedded in a tkinter parent widget.

    Creates a Figure, attaches it to a FigureCanvasTkAgg, and packs
    the canvas widget into the given parent frame.
    """

    def __init__(self, parent):
        self._fig = Figure(figsize=(6, 3.2), dpi=96, facecolor="#222222")
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._fig, master=parent)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._draw_empty("Vyberte předmět")

    def update(self, distributions: list[GradeDistribution]) -> None:
        """Redraw the chart for the given list of semester distributions."""
        self._ax.clear()
        if not distributions:
            self._draw_empty("Pro tento předmět nejsou data")
            return

        # All distributions for one course share the same grade keys.
        grade_keys = list(distributions[0].grades.keys())
        n_semesters = len(distributions)
        x = np.arange(len(grade_keys))
        # Divide the available bar width evenly among semesters.
        width = 0.8 / n_semesters

        for i, dist in enumerate(distributions):
            counts = [dist.grades[g] for g in grade_keys]
            offset = (i - n_semesters / 2 + 0.5) * width
            color = BAR_COLORS[i % len(BAR_COLORS)]
            self._ax.bar(x + offset, counts, width, label=dist.semester_name,
                         color=color, alpha=0.85)

        self._ax.set_xticks(x)
        self._ax.set_xticklabels(grade_keys, color="white")
        self._ax.set_ylabel("Počet studentů", color="white", fontsize=9)
        self._ax.tick_params(colors="white")
        # Force integer ticks — fractional student counts make no sense.
        self._ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        self._ax.set_facecolor("#2b2b2b")
        self._ax.spines[:].set_color("#555555")
        self._ax.legend(
            fontsize=7, facecolor="#333333", labelcolor="white", framealpha=0.7
        )
        self._fig.tight_layout()
        self._canvas.draw()

    def clear(self) -> None:
        self._ax.clear()
        self._draw_empty("Vyberte předmět")

    def _draw_empty(self, message="Žádná data") -> None:
        """Show a centred placeholder message with no axes."""
        self._ax.set_facecolor("#2b2b2b")
        self._ax.set_xticks([])
        self._ax.set_yticks([])
        self._ax.text(
            0.5, 0.5, message,
            transform=self._ax.transAxes,
            ha="center", va="center", color="#888888", fontsize=12,
        )
        self._ax.tick_params(colors="#555555")
        self._ax.spines[:].set_color("#444444")
        self._fig.tight_layout()
        self._canvas.draw()
