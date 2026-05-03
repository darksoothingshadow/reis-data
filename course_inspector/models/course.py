class GradeDistribution:
    """Grade counts for one semester (aggregate term 'Všechny termíny').

    evaluation_type is either 'exam' (grades A-F/FN) or 'credit' (Zap/Nezap).
    """

    def __init__(self, semester_name, year, grades: dict, evaluation_type: str):
        self.semester_name = semester_name
        self.year = year
        self.grades = grades
        self.evaluation_type = evaluation_type
        self.total = sum(grades.values())
        failing = grades.get("F", 0) + grades.get("FN", 0) + grades.get("Nezap", 0)
        self.fail_rate = failing / self.total if self.total > 0 else 0.0


class Course:
    """One MENDELU course with lazily loaded grade distributions."""

    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.distributions: list[GradeDistribution] = []

    def __str__(self):
        return f"{self.code} — {self.name}"
