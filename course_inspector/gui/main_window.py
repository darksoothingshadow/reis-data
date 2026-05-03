import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from data.repository import CourseRepository
from data.saved_list import SavedList
from gui.grade_chart import GradeChart


class MainWindow:
    """Main application window with search, chart, and saved courses panel."""

    def __init__(self, repository: CourseRepository, saved_list: SavedList):
        self._repo = repository
        self._saved = saved_list
        self._current_course = None
        self._search_results = []

        self._root = ttk.Window(themename="darkly")
        self._root.title("MENDELU Lupa")
        self._root.geometry("1000x680")
        self._root.minsize(800, 560)

        self._build_ui()
        self._refresh_saved_list()

    # ------------------------------------------------------------------ build

    def _build_ui(self) -> None:
        outer = ttk.Frame(self._root, padding=8)
        outer.pack(fill=BOTH, expand=YES)

        ttk.Label(outer, text="MENDELU Lupa", font=("Segoe UI", 16, "bold"),
                  bootstyle="info").pack(anchor=W, pady=(0, 6))

        panes = ttk.Panedwindow(outer, orient=HORIZONTAL)
        panes.pack(fill=BOTH, expand=YES)

        panes.add(self._build_left(panes), weight=1)
        panes.add(self._build_right(panes), weight=3)

    def _build_left(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=(0, 0, 8, 0))

        ttk.Label(frame, text="Hledat předmět:").pack(anchor=W)
        self._search_var = tk.StringVar()
        search_entry = ttk.Entry(frame, textvariable=self._search_var)
        search_entry.pack(fill=X, pady=(2, 4))
        search_entry.bind("<KeyRelease>", self._on_search)

        ttk.Label(frame, text="Výsledky hledání:").pack(anchor=W)
        result_frame = ttk.Frame(frame)
        result_frame.pack(fill=BOTH, expand=YES, pady=(2, 8))

        scrollbar = ttk.Scrollbar(result_frame, orient=VERTICAL)
        self._result_list = tk.Listbox(
            result_frame, yscrollcommand=scrollbar.set,
            bg="#2b2b2b", fg="white", selectbackground="#375a7f",
            relief="flat", borderwidth=0, font=("Segoe UI", 9),
        )
        scrollbar.config(command=self._result_list.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self._result_list.pack(side=LEFT, fill=BOTH, expand=YES)
        self._result_list.bind("<<ListboxSelect>>", self._on_select_result)

        ttk.Separator(frame).pack(fill=X, pady=4)
        ttk.Label(frame, text="Oblíbené:", bootstyle="warning").pack(anchor=W)
        saved_frame = ttk.Frame(frame)
        saved_frame.pack(fill=BOTH, expand=YES, pady=(2, 0))

        saved_scroll = ttk.Scrollbar(saved_frame, orient=VERTICAL)
        self._saved_list_widget = tk.Listbox(
            saved_frame, yscrollcommand=saved_scroll.set,
            bg="#2b2b2b", fg="#ffc107", selectbackground="#856404",
            relief="flat", borderwidth=0, font=("Segoe UI", 9),
        )
        saved_scroll.config(command=self._saved_list_widget.yview)
        saved_scroll.pack(side=RIGHT, fill=Y)
        self._saved_list_widget.pack(side=LEFT, fill=BOTH, expand=YES)
        self._saved_list_widget.bind("<<ListboxSelect>>", self._on_select_saved)

        return frame

    def _build_right(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=(8, 0, 0, 0))

        self._course_label = ttk.Label(
            frame, text="Žádný předmět nevybrán",
            font=("Segoe UI", 12, "bold"), wraplength=600,
        )
        self._course_label.pack(anchor=W)

        self._stats_label = ttk.Label(frame, text="", bootstyle="secondary")
        self._stats_label.pack(anchor=W, pady=(2, 6))

        chart_frame = ttk.LabelFrame(frame, text="Rozložení známek (poslední 3 semestry)")
        chart_frame.pack(fill=BOTH, expand=YES)
        self._chart = GradeChart(chart_frame)

        bottom = ttk.Frame(frame)
        bottom.pack(fill=X, pady=(8, 0))

        # note section
        note_frame = ttk.LabelFrame(bottom, text="Poznámka")
        note_frame.pack(fill=X)

        self._note_text = tk.Text(
            note_frame, height=4, bg="#2b2b2b", fg="white",
            insertbackground="white", relief="flat", font=("Segoe UI", 9),
        )
        self._note_text.pack(fill=X)

        btn_row = ttk.Frame(bottom)
        btn_row.pack(fill=X, pady=(6, 0))

        self._add_btn = ttk.Button(
            btn_row, text="+ Přidat do oblíbených", bootstyle="success-outline",
            command=self._on_save_course,
        )
        self._add_btn.pack(side=LEFT, padx=(0, 4))

        self._remove_btn = ttk.Button(
            btn_row, text="− Odebrat z oblíbených", bootstyle="danger-outline",
            command=self._on_remove_saved,
        )
        self._remove_btn.pack(side=LEFT, padx=(0, 4))

        ttk.Button(
            btn_row, text="Uložit poznámku", bootstyle="warning-outline",
            command=self._on_save_note,
        ).pack(side=LEFT, padx=(0, 4))

        ttk.Button(
            btn_row, text="Smazat poznámku", bootstyle="secondary-outline",
            command=self._on_delete_note,
        ).pack(side=LEFT)

        return frame

    # --------------------------------------------------------------- handlers

    def _on_search(self, _event=None) -> None:
        query = self._search_var.get().strip()
        self._result_list.delete(0, END)
        if len(query) < 1:
            return
        results = self._repo.search(query)
        self._search_results = results
        for course in results:
            self._result_list.insert(END, f"{course.code}  {course.name}")

    def _on_select_result(self, _event=None) -> None:
        sel = self._result_list.curselection()
        if not sel:
            return
        course = self._search_results[sel[0]]
        self._load_course(course)

    def _on_select_saved(self, _event=None) -> None:
        sel = self._saved_list_widget.curselection()
        if not sel:
            return
        code = self._saved.get_all()[sel[0]].code
        course = self._repo.get_by_code(code)
        if course:
            self._load_course(course)

    def _load_course(self, course) -> None:
        self._current_course = course
        self._repo.load_distributions(course)

        self._course_label.config(text=str(course))

        if course.distributions:
            avg_fail = sum(d.fail_rate for d in course.distributions) / len(course.distributions)
            total_students = sum(d.total for d in course.distributions)
            self._stats_label.config(
                text=f"Průměrná míra neúspěchu: {avg_fail:.0%}  |  Celkem záznamů: {total_students}"
            )
        else:
            self._stats_label.config(text="Žádná data k dispozici")

        self._chart.update(course.distributions)

        note = self._saved.get_note(course.code)
        self._note_text.delete("1.0", END)
        self._note_text.insert("1.0", note)

    def _on_save_course(self) -> None:
        if self._current_course:
            self._saved.add(self._current_course.code)
            self._refresh_saved_list()

    def _on_remove_saved(self) -> None:
        if self._current_course:
            self._saved.remove(self._current_course.code)
            self._refresh_saved_list()

    def _on_save_note(self) -> None:
        if self._current_course:
            note = self._note_text.get("1.0", END).strip()
            self._saved.add(self._current_course.code)  # ensure it's saved first
            self._saved.set_note(self._current_course.code, note)
            self._refresh_saved_list()

    def _on_delete_note(self) -> None:
        if self._current_course:
            self._note_text.delete("1.0", END)
            self._saved.set_note(self._current_course.code, "")

    def _refresh_saved_list(self) -> None:
        self._saved_list_widget.delete(0, END)
        for entry in self._saved.get_all():
            marker = " ✎" if entry.note else ""
            self._saved_list_widget.insert(END, f"{entry.code}{marker}")

    # -------------------------------------------------------------------- run

    def run(self) -> None:
        self._root.mainloop()
        self._repo.close()
