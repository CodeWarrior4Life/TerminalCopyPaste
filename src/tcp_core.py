"""TCP core orchestrator -- stateless CLI entry point."""

import sys
import webbrowser

from src.clipboard import (
    has_image_in_clipboard,
    get_clipboard_image,
    has_files_in_clipboard,
    get_clipboard_files,
)
from src.config import load_config, TCPConfig
from src.file_resolver import find_recent_screenshot, save_clipboard_image
from src.path_format import format_path
from src.screenshot_dir import get_screenshot_dir
from src.usage import UsageTracker


def run(
    config: TCPConfig | None = None, data_dir: str | None = None
) -> tuple[int, str]:
    """Main entry point. Returns (exit_code, output_string)."""
    try:
        if config is None:
            config = load_config()

        # Files/virtual files (v1.1). Runs before image path so apps
        # that publish both an image preview AND a file yield the file.
        if has_files_in_clipboard():
            file_paths = get_clipboard_files()
            if file_paths:
                formatted = "\n".join(format_path(p, config) for p in file_paths)
                tracker = UsageTracker(data_dir=data_dir)
                tracker.increment()
                if tracker.should_prompt():
                    _show_coffee_prompt(tracker)
                return 0, formatted
            # get_clipboard_files returned None -> fall through to image path

        if not has_image_in_clipboard():
            return 1, ""

        screenshot_dir = get_screenshot_dir(config)

        # Step 1: Check for a recent backing file
        path = find_recent_screenshot(screenshot_dir, config.recency_window)

        # Step 2: If no backing file, save clipboard image
        if path is None:
            image = get_clipboard_image()
            if image is None:
                return 1, ""
            path = save_clipboard_image(image, screenshot_dir, config)

        formatted = format_path(path, config)

        # Track usage
        tracker = UsageTracker(data_dir=data_dir)
        tracker.increment()

        # Check for milestone prompt
        if tracker.should_prompt():
            _show_coffee_prompt(tracker)

        return 0, formatted

    except Exception as e:
        print(f"TCP error: {e}", file=sys.stderr)
        return 2, ""


def _show_coffee_prompt(tracker: UsageTracker) -> None:
    """Show milestone coffee prompt -- fire-and-forget, never blocks path output."""
    try:
        import subprocess
        from src.usage import BMAC_URL

        # Fire-and-forget: open browser without blocking the CLI
        subprocess.Popen(
            [sys.executable, "-c", f"import webbrowser; webbrowser.open('{BMAC_URL}')"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        tracker.mark_prompted()
    except Exception:
        pass  # Never let a prompt failure break the tool


def main() -> None:
    """CLI entry point."""
    exit_code, output = run()
    if output:
        print(output, end="")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
