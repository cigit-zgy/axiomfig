#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from axiomfig.typography import discover_fonts

if __name__ == "__main__":
    for role, font in discover_fonts().items():
        print(f"PASS {role}: {font.family} [{font.matplotlib_family}] -> {font.path}")
