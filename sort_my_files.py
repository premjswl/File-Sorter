import json
import os
import shutil
from datetime import datetime
from pathlib import Path

DRY_RUN = False

FILE_BLUEPRINT = {
    ".jpg": "Photos", ".jpeg": "Photos", ".png": "Photos", ".gif": "Photos",
    ".webp": "Photos", ".bmp": "Photos", ".heic": "Photos", ".svg": "Photos",
    ".pdf": "Docs", ".docx": "Docs", ".doc": "Docs", ".txt": "Docs",
    ".rtf": "Docs", ".odt": "Docs", ".md": "Docs",
    ".xlsx": "Spreadsheets", ".xls": "Spreadsheets", ".csv": "Spreadsheets",
    ".pptx": "Presentations", ".ppt": "Presentations", ".key": "Presentations",
    ".mp3": "Music", ".wav": "Music", ".flac": "Music", ".m4a": "Music",
    ".mp4": "Videos", ".mov": "Videos", ".mkv": "Videos", ".avi": "Videos",
    ".zip": "Zipped_Files", ".rar": "Zipped_Files", ".7z": "Zipped_Files",
    ".tar": "Zipped_Files", ".gz": "Zipped_Files",
    ".exe": "Installers", ".msi": "Installers", ".dmg": "Installers", ".pkg": "Installers",
}

NEVER_MOVE = {".lnk", ".ini", ".tmp", ".crdownload", ".part", ".url", ".app"}

home = Path.home()
CANDIDATE_FOLDERS = [
    home / "Desktop",
    home / "OneDrive" / "Desktop",
    home / "Downloads",
    home / "Documents",
]

LOG_DIR = home / "file_sort_logs"
MOVE_LOG = []
CREATED_FOLDERS = []


def unique_destination(folder: Path, filename: str) -> Path:
    """If a file with the same name exists, add (1), (2)... instead of overwriting."""
    dest = folder / filename
    if not dest.exists():
        return dest
    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 1
    while True:
        dest = folder / f"{stem} ({counter}){suffix}"
        if not dest.exists():
            return dest
        counter += 1


def sort_folder(base: Path) -> int:
    moved = 0
    print(f"\n=== {base} ===")

    for item in base.iterdir():
        if not item.is_file():
            continue
        if item.name.startswith("."):
            continue
        if item.resolve() == Path(__file__).resolve():
            continue

        ext = item.suffix.lower()
        if ext in NEVER_MOVE or ext not in FILE_BLUEPRINT:
            continue

        target_folder = base / FILE_BLUEPRINT[ext]
        destination = unique_destination(target_folder, item.name)

        if DRY_RUN:
            print(f"[preview] {item.name}  ->  {FILE_BLUEPRINT[ext]}/")
        else:
            try:
                if not target_folder.exists():
                    target_folder.mkdir()
                    CREATED_FOLDERS.append(str(target_folder))
                original_path = str(item)
                shutil.move(str(item), str(destination))
                MOVE_LOG.append({"original": original_path, "moved_to": str(destination)})
                print(f"Moved {item.name}  ->  {FILE_BLUEPRINT[ext]}/")
            except (PermissionError, OSError) as err:
                print(f"Skipped {item.name} (in use or locked): {err}")
                continue
        moved += 1
    return moved


def main():
    seen = set()
    total = 0
    for folder in CANDIDATE_FOLDERS:
        if folder.exists() and folder.resolve() not in seen:
            seen.add(folder.resolve())
            total += sort_folder(folder)

    if not DRY_RUN and MOVE_LOG:
        LOG_DIR.mkdir(exist_ok=True)
        log_file = LOG_DIR / f"move_log_{datetime.now():%Y-%m-%d_%H-%M-%S}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump({"moves": MOVE_LOG, "created_folders": CREATED_FOLDERS}, f, indent=2)
        print(f"\nUndo log saved: {log_file}")
        print("To undo this run, use restore_my_files.py")

    label = "would be moved" if DRY_RUN else "moved"
    print(f"\nDone. {total} file(s) {label}.")
    if DRY_RUN:
        print("This was a preview. Set DRY_RUN = False to actually move files.")


if __name__ == "__main__":
    main()