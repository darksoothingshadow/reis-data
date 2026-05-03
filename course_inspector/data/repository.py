import sqlite3
from pathlib import Path

from models.course import Course, GradeDistribution

_DB_PATH = Path(__file__).parent.parent.parent / "success-rates.db"


class CourseRepository:
    """Reads course data from the local SQLite snapshot."""

    def __init__(self, db_path=_DB_PATH):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def search(self, query: str) -> list[Course]:
        """Return up to 50 courses whose code or name contains the query."""
        pattern = f"%{query}%"
        sql = """
            SELECT DISTINCT code, name
            FROM courses
            WHERE code LIKE ? OR name LIKE ?
            ORDER BY code
            LIMIT 50
        """
        rows = self._conn.execute(sql, (pattern, pattern)).fetchall()
        return [Course(r["code"], r["name"]) for r in rows]

    def load_distributions(self, course: Course, n: int = 3) -> None:
        """Fill course.distributions with data from the last n semesters."""
        sql = """
            SELECT s.name AS sem_name, s.year, sr.evaluation_type,
                   sr.grade_a, sr.grade_b, sr.grade_c, sr.grade_d,
                   sr.grade_e, sr.grade_f, sr.grade_fn,
                   sr.grade_zap, sr.grade_nezap
            FROM success_rates sr
            JOIN courses c ON sr.course_id = c.id
            JOIN semesters s ON sr.semester_id = s.id
            WHERE c.code = ?
              AND sr.term_name = 'Všechny termíny'
            ORDER BY s.year DESC, s.id DESC
            LIMIT ?
        """
        rows = self._conn.execute(sql, (course.code, n)).fetchall()
        course.distributions = []
        for r in rows:
            if r["evaluation_type"] == "credit":
                grades = {"Zap": r["grade_zap"], "Nezap": r["grade_nezap"]}
            else:
                grades = {
                    "A": r["grade_a"], "B": r["grade_b"], "C": r["grade_c"],
                    "D": r["grade_d"], "E": r["grade_e"], "F": r["grade_f"],
                    "FN": r["grade_fn"],
                }
            course.distributions.append(
                GradeDistribution(r["sem_name"], r["year"], grades, r["evaluation_type"])
            )

    def get_by_code(self, code: str) -> "Course | None":
        """Return a single Course by exact code, or None if not found."""
        row = self._conn.execute(
            "SELECT code, name FROM courses WHERE code = ? LIMIT 1", (code,)
        ).fetchone()
        return Course(row["code"], row["name"]) if row else None

    def close(self) -> None:
        self._conn.close()
