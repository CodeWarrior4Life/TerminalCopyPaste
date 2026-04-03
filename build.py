"""Build TCP into standalone executables."""

import subprocess
import sys
from pathlib import Path


def build():
    dist = Path("dist")
    dist.mkdir(exist_ok=True)

    print("Building tcp_core.exe...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--name",
            "tcp_core",
            "--distpath",
            str(dist),
            "--specpath",
            str(dist),
            "--clean",
            "src/tcp_core.py",
        ],
        check=True,
    )

    print("\nBuild complete!")
    print(f"  tcp_core.exe -> {dist / 'tcp_core.exe'}")
    print(f"  tcp.ahk      -> src/platforms/windows/tcp.ahk")
    print("\nTo distribute: zip tcp_core.exe + tcp.ahk + LICENSE")


if __name__ == "__main__":
    build()
