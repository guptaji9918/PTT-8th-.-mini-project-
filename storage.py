import json
from pathlib import Path

from library_service import LibraryManager


class JSONStorage:
    def _init_(self, file_path="data.json"):
        self.file_path = Path(file_path)

    def save(self, manager):
        try:
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(manager.to_dict(), file, indent=4)
        except OSError as error:
            raise OSError(f"Could not save library data: {error}") from error

    def load(self):
        if not self.file_path.exists():
            return LibraryManager()
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return LibraryManager.from_dict(data)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Could not load valid library data: {error}") from error