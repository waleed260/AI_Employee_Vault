#!/usr/bin/env python3
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. Run: pip install watchdog")

sys.path.insert(0, str(Path(__file__).parent.parent))
from watchers.base_watcher import BaseWatcher


class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str, drop_folder: Path):
        self.needs_action = Path(vault_path) / "Needs_Action"
        self.drop_folder = drop_folder
        self.vault_path = Path(vault_path)
        self.logger = (
            BaseWatcher.__dict__["__init__"]
            .__globals__["logging"]
            .getLogger("DropFolderHandler")
        )

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        if source.parent != self.drop_folder:
            return
        self._process_file(source)

    def on_modified(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        if source.parent == self.drop_folder and source.suffix:
            self._process_file(source)

    def _process_file(self, source: Path):
        try:
            safe_name = source.name.replace("/", "-").replace("\\", "-")
            dest = self.needs_action / f"FILE_{safe_name}"
            shutil.copy2(source, dest)

            meta_path = dest.with_suffix(".md")
            meta_content = f"""---
type: file_drop
source: drop_folder
original_name: {source.name}
size: {source.stat().st_size}
copied_at: {datetime.now().isoformat()}
status: pending
---

## File Dropped for Processing

- **Original path**: {source}
- **Size**: {source.stat().st_size:,} bytes
- **Type**: {source.suffix or "unknown"}

## Notes

_AI Employee will analyze this file and create appropriate actions_
"""
            meta_path.write_text(meta_content)
            print(f"[DropFolderHandler] Copied {source.name} to vault")

        except Exception as e:
            print(f"[DropFolderHandler] Error processing {source}: {e}")


class FileSystemWatcher:
    def __init__(self, vault_path: str, drop_folder: str):
        self.vault_path = Path(vault_path)
        self.drop_folder = Path(drop_folder)
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        self.observer = Observer()
        self.handler = DropFolderHandler(vault_path, self.drop_folder)

    def run(self):
        print(f"[FileSystemWatcher] Starting - monitoring: {self.drop_folder}")
        self.observer.schedule(self.handler, str(self.drop_folder), recursive=False)
        self.observer.start()
        try:
            while True:
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


def main():
    parser = argparse.ArgumentParser(description="File System Watcher for AI Employee")
    parser.add_argument("--vault", required=True, help="Path to Obsidian vault")
    parser.add_argument(
        "--drop-folder", required=True, help="Folder to monitor for drops"
    )
    args = parser.parse_args()

    if not WATCHDOG_AVAILABLE:
        print("Error: watchdog library required. Run: pip install watchdog")
        sys.exit(1)

    watcher = FileSystemWatcher(args.vault, args.drop_folder)
    watcher.run()


if __name__ == "__main__":
    main()
