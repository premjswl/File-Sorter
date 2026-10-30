import json
import shutil
import sys
from pathlib import Path

DRY_RUN = True

LOG_DIR = Path.home() / "file_sort_logs"

LOG_FILE = None


def find_log() -> Path:
    if LOG_FILE:
        return Path(LOG_FILE)
    logs = sorted(LOG_DIR.glob("move_log_*.json"))
    if not logs:
        print(f"No undo logs found in {LOG_DIR}.")
        print("A log is only created when sort_my_files.py runs with DRY_RUN = False.")
        sys.exit(1)
    return logs[-1]


def unique_path(path: Path) -> Path:
    """Avoid overwriting if something new now sits at the original location."""
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem} (restored {counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def main():
    log_path = find_log()
    print(f"Using log: {log_path.name}")

    with open(log_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    restored = 0
    skipped = 0

    for move in reversed(data["moves"]):
        current = Path(move["moved_to"])
        original = Path(move["original"])

        if not current.exists():
            print(f"[skip] Not found (moved or deleted since): {current}")
            skipped += 1
            continue

        target = unique_path(original)

        if DRY_RUN:
            print(f"[preview] {current.name}  ->  {target.parent}")
        else:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(current), str(target))
                print(f"Restored {target.name}  ->  {target.parent}")
            except (PermissionError, OSError) as err:
                print(f"[skip] Could not restore {current.name}: {err}")
                skipped += 1
                continue
        restored += 1

    if not DRY_RUN:
        for folder in data.get("created_folders", []):
            folder = Path(folder)
            try:
                if folder.exists() and not any(folder.iterdir()):
                    folder.rmdir()
                    print(f"Removed empty folder: {folder}")
            except OSError:
                pass

        log_path.rename(log_path.with_suffix(".json.restored"))

    label = "would be restored" if DRY_RUN else "restored"
    print(f"\nDone. {restored} file(s) {label}, {skipped} skipped.")
    if DRY_RUN:
        print("This was a preview. Set DRY_RUN = False to actually restore.")


if __name__ == "__main__":
    main()