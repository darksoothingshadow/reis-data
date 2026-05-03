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
            SELECT s.name AS sem_name, s.year,
                   sr.grade_a, sr.grade_b, sr.grade_c, sr.grade_d,
                   sr.grade_e, sr.grade_f, sr.grade_fn
            FROM success_rates sr
            JOIN courses c ON sr.course_id = c.id
            JOIN semesters s ON sr.semester_id = s.id
            WHERE c.code = ?
              AND sr.term_name = 'Všechny termíny'
            ORDER BY s.year DESC, s.id DESC
            LIMIT ?
        """
        rows = self._conn.execute(sql, (course.code, n)).fetchall()
        course.distributions = [
            GradeDistribution(
                r["sem_name"], r["year"],
                r["grade_a"], r["grade_b"], r["grade_c"], r["grade_d"],
                r["grade_e"], r["grade_f"], r["grade_fn"],
            )
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()
