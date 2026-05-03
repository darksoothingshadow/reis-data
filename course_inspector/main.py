from pathlib import Path

from data.repository import CourseRepository
from data.saved_list import SavedList
from gui.main_window import MainWindow

_SAVED_PATH = Path(__file__).parent / "saved.json"


def main():
    repository = CourseRepository()
    saved_list = SavedList(_SAVED_PATH)
    window = MainWindow(repository, saved_list)
    window.run()


if __name__ == "__main__":
    main()
