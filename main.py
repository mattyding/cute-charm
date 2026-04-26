#!/usr/bin/env python3
"""
Cute Charm Gen 4 Tool
=====================
Cross-platform (Mac/Linux/Windows) utility for generating Gen 4 Pokémon save
files with the Cute Charm glitch set up correctly.

Two modes:
  Direct Inject  – patches TID/SID/name directly into an existing save file.
  RNG Manip      – outputs EonTimer settings + step-by-step instructions for
                   obtaining the same TID/SID through legitimate RNG manipulation.

Save-file logic ported from PKHeX.Core (MIT):
  https://github.com/kwsch/PKHeX

Requires:  Python 3.10+, PyQt6
Install:   pip install PyQt6
Run:       python main.py
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Cute Charm Gen 4 Tool")
    app.setOrganizationName("cutecharm")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
