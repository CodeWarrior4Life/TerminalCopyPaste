"""Clipboard image detection and extraction."""

import sys
from PIL import Image


def has_image_in_clipboard() -> bool:
    if sys.platform == "win32":
        return _win32_has_image()
    elif sys.platform == "darwin":
        return _macos_has_image()
    else:
        return _linux_has_image()


def get_clipboard_image() -> Image.Image | None:
    if sys.platform == "win32":
        return _win32_get_image()
    elif sys.platform == "darwin":
        return _macos_get_image()
    else:
        return _linux_get_image()


def _win32_has_image() -> bool:
    import win32clipboard

    try:
        win32clipboard.OpenClipboard()
        has = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB)
        return bool(has)
    except Exception:
        return False
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _win32_get_image() -> Image.Image | None:
    import win32clipboard
    import io

    try:
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            return None
        data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
        # CF_DIB is a BMP without the file header; Pillow's BmpImagePlugin handles it
        # We need to add the BMP file header
        bmp_header = _make_bmp_header(data)
        return Image.open(io.BytesIO(bmp_header + data))
    except Exception:
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _make_bmp_header(dib_data: bytes) -> bytes:
    import struct

    dib_header_size = struct.unpack_from("<I", dib_data, 0)[0]
    file_size = 14 + len(dib_data)
    pixel_offset = 14 + dib_header_size
    return struct.pack("<2sIHHI", b"BM", file_size, 0, 0, pixel_offset)


def _macos_has_image() -> bool:
    try:
        import subprocess

        result = subprocess.run(
            ["osascript", "-e", "clipboard info for (class PNGf)"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _macos_get_image() -> Image.Image | None:
    try:
        import subprocess
        import io

        result = subprocess.run(
            [
                "osascript",
                "-e",
                "set png to (the clipboard as «class PNGf»)\nreturn png",
            ],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            return Image.open(io.BytesIO(result.stdout))
    except Exception:
        pass
    return None


def _linux_has_image() -> bool:
    try:
        import subprocess

        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and "image/png" in result.stdout
    except Exception:
        return False


def _linux_get_image() -> Image.Image | None:
    try:
        import subprocess
        import io

        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            return Image.open(io.BytesIO(result.stdout))
    except Exception:
        pass
    return None


def has_files_in_clipboard() -> bool:
    if sys.platform == "win32":
        return _win32_has_files()
    return False


def get_clipboard_files() -> list[str] | None:
    if sys.platform != "win32":
        return None
    paths = _win32_get_hdrop_paths()
    if paths:
        return paths
    return _win32_get_virtual_files()


def _win32_has_files() -> bool:
    import win32clipboard

    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
            return True
        try:
            cf_descriptor = win32clipboard.RegisterClipboardFormat(
                "FileGroupDescriptorW"
            )
            if win32clipboard.IsClipboardFormatAvailable(cf_descriptor):
                return True
        except Exception:
            pass
        return False
    except Exception:
        return False
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _win32_get_hdrop_paths() -> list[str] | None:
    import win32clipboard

    try:
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
            return None
        data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
        paths = [str(p) for p in data]
        return paths if paths else None
    except Exception:
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _win32_get_virtual_files() -> list[str] | None:
    """Extract virtual files from clipboard (FileGroupDescriptorW + FileContents)
    to the TCP temp dir. Handles the single-file case common in messaging apps."""
    import win32clipboard
    import struct
    from src.file_resolver import save_clipboard_blob

    try:
        cf_descriptor = win32clipboard.RegisterClipboardFormat("FileGroupDescriptorW")
        cf_contents = win32clipboard.RegisterClipboardFormat("FileContents")
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(cf_descriptor):
            return None
        descriptor_blob = win32clipboard.GetClipboardData(cf_descriptor)
        if not descriptor_blob:
            return None

        # Parse FILEGROUPDESCRIPTORW: UINT cItems, then FILEDESCRIPTORW[cItems]
        (count,) = struct.unpack_from("<I", descriptor_blob, 0)
        if count < 1:
            return None
        # Each FILEDESCRIPTORW is 592 bytes; cFileName is at offset 72, 260 wchars
        filenames = []
        record_size = 592
        name_offset = 72
        name_byte_len = 260 * 2
        for i in range(count):
            base = 4 + i * record_size
            raw_name = descriptor_blob[
                base + name_offset : base + name_offset + name_byte_len
            ]
            name = raw_name.decode("utf-16-le", errors="replace").split("\x00", 1)[0]
            if name:
                filenames.append(name)

        if not filenames:
            return None

        # pywin32's GetClipboardData for FileContents returns the first stream's bytes.
        # Multi-file virtual paste requires IDataObject; defer to v1.2.
        contents = win32clipboard.GetClipboardData(cf_contents)
        if contents is None:
            return None

        saved = save_clipboard_blob(filenames[0], contents)
        return [saved]
    except Exception:
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
