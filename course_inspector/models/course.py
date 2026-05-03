class GradeDistribution:
    """Grade counts for one semester (aggregate term 'Všechny termíny')."""

    GRADE_KEYS = ("A", "B", "C", "D", "E", "F", "FN")

    def __init__(self, semester_name, year, a, b, c, d, e, f, fn):
        self.semester_name = semester_name
        self.year = year
        self.grades = {"A": a, "B": b, "C": c, "D": d, "E": e, "F": f, "FN": fn}
        self.total = sum(self.grades.values())
        failing = f + fn
        self.fail_rate = failing / self.total if self.total > 0 else 0.0


class Course:
    """One MENDELU course with lazily loaded grade distributions."""

    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.distributions: list[GradeDistribution] = []

    def __str__(self):
        return f"{self.code} — {self.name}"
