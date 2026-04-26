"""
Main application window for the Cute Charm Gen 4 Save Tool.
"""

from __future__ import annotations
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QRadioButton, QButtonGroup, QComboBox,
    QGroupBox, QTabWidget, QPushButton, QFileDialog, QTextEdit,
    QSizePolicy, QFrame, QMessageBox, QToolButton, QSpinBox, QStyle,
    QStyleOptionGroupBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.cute_charm import (
    shiny_groups, find_tid_sid, GENDER_RATIOS,
)
from core.gen4_encoding import validate_name
from core.gen4_save import patch_save, GAME_CONFIGS
from core.rng_timer import find_seed_for_tid_sid, build_instructions, build_tas_instructions
from ui.info_dialog import InfoDialog


GAMES = ["Diamond", "Pearl", "Platinum", "HeartGold", "SoulSilver"]
_GENDER_RATIO_NAMES = list(GENDER_RATIOS.keys())

_GROUP_TITLE_STYLE = "QGroupBox { font-size: 13pt; font-weight: bold; }"

_HELP_BTN_STYLE = """
    QToolButton {
        border: 1.5px solid #888;
        border-radius: 10px;
        font-weight: bold;
        font-size: 11px;
        color: #555;
        background: transparent;
    }
    QToolButton:hover {
        border-color: #0078d4;
        color: #0078d4;
        background: rgba(0, 120, 212, 0.08);
    }
    QToolButton:pressed {
        background: rgba(0, 120, 212, 0.18);
    }
"""


class _HelpGroupBox(QGroupBox):
    """QGroupBox with a ? button positioned inline with the title text."""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self._help_btn = QToolButton(self)
        self._help_btn.setText("?")
        self._help_btn.setFixedSize(20, 20)
        self._help_btn.setStyleSheet(_HELP_BTN_STYLE)
        self._help_btn.setToolTip("What is the Cute Charm glitch?")

    @property
    def help_button(self) -> QToolButton:
        return self._help_btn

    def resizeEvent(self, event):
        super().resizeEvent(event)
        opt = QStyleOptionGroupBox()
        self.initStyleOption(opt)
        label_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_GroupBox,
            opt,
            QStyle.SubControl.SC_GroupBoxLabel,
            self,
        )
        text_w = self.fontMetrics().horizontalAdvance(self.title())
        x = label_rect.left() + text_w + 8
        y = label_rect.top() + (label_rect.height() - self._help_btn.height()) // 2
        self._help_btn.move(x, y)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gen 4 Cute Charm Glitch Tool")
        self.setMinimumSize(760, 600)
        self._build_ui()
        self._refresh_groups()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Game:"))
        self._game_combo = QComboBox()
        self._game_combo.addItem("Select game…")
        self._game_combo.addItems(GAMES)
        self._game_combo.setCurrentIndex(0)
        self._game_combo.currentTextChanged.connect(self._on_settings_changed)
        top_row.addWidget(self._game_combo)
        top_row.addSpacing(24)
        top_row.addWidget(QLabel("Preferred TID (optional):"))
        self._tid_spin = QSpinBox()
        self._tid_spin.setRange(0, 65535)
        self._tid_spin.setSpecialValueText("Auto")
        self._tid_spin.setValue(0)
        self._tid_spin.valueChanged.connect(self._on_settings_changed)
        top_row.addWidget(self._tid_spin)
        top_row.addStretch()
        outer.addLayout(top_row)

        outer.addWidget(self._build_cute_charm_group())
        outer.addSpacing(6)

        result_box = QGroupBox("Calculated TID / SID")
        result_box.setStyleSheet(_GROUP_TITLE_STYLE)
        rl = QHBoxLayout(result_box)
        rl.setContentsMargins(8, 6, 8, 8)
        self._tid_label = QLabel("TID: —")
        self._sid_label = QLabel("SID: —")
        self._tsv_label = QLabel("TSV: —")
        for lbl in (self._tid_label, self._sid_label, self._tsv_label):
            f = lbl.font(); f.setBold(True); f.setPointSize(13); lbl.setFont(f)
            rl.addWidget(lbl)
        rl.addStretch()
        outer.addWidget(result_box)

        tabs = QTabWidget()
        tabs.addTab(self._build_rng_tab(),    "RNG Manipulation")
        tabs.addTab(self._build_inject_tab(), "Direct Inject")
        outer.addWidget(tabs, stretch=1)

    def _build_cute_charm_group(self) -> QGroupBox:
        box = _HelpGroupBox("Cute Charm Setup")
        box.setStyleSheet(_GROUP_TITLE_STYLE)
        box.help_button.clicked.connect(self._show_info)
        vl = QVBoxLayout(box)
        vl.setSpacing(8)
        vl.setContentsMargins(8, 6, 8, 8)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Lead Gender:"))
        self._lead_male   = QRadioButton("Male")
        self._lead_female = QRadioButton("Female")
        self._lead_female.setChecked(True)
        self._lead_group = QButtonGroup()
        self._lead_group.addButton(self._lead_male,   0)
        self._lead_group.addButton(self._lead_female, 1)
        self._lead_male.toggled.connect(self._on_settings_changed)
        row1.addWidget(self._lead_male)
        row1.addWidget(self._lead_female)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Target Ratio:"))
        self._ratio_combo = QComboBox()
        self._ratio_combo.addItems(_GENDER_RATIO_NAMES)
        self._ratio_combo.setCurrentIndex(2)  # default 50/50
        self._ratio_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._ratio_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        row1.addWidget(self._ratio_combo, stretch=1)
        vl.addLayout(row1)

        vl.addWidget(QLabel("Shiny Group (pick the natures you want):"))

        self._group_radios: list[QRadioButton] = []
        self._group_data: list[dict] = []
        self._group_btn_group = QButtonGroup()
        groups_frame = QFrame()
        groups_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._groups_layout = QVBoxLayout(groups_frame)
        self._groups_layout.setContentsMargins(8, 6, 8, 6)
        self._groups_layout.setSpacing(4)
        vl.addWidget(groups_frame, stretch=1)

        return box

    def _build_rng_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(12, 12, 12, 12)
        vl.setSpacing(10)

        note = QLabel(
            "Outputs step-by-step instructions for obtaining the TID/SID through "
            "RNG manipulation or frame-perfect TAS input. You will need EonTimer "
            "and PokéFinder."
        )
        note.setWordWrap(True)
        vl.addWidget(note)

        trainer_row = QHBoxLayout()
        trainer_row.addWidget(QLabel("Trainer name (max 7):"))
        self._name_edit = QLineEdit()
        self._name_edit.setMaxLength(7)
        self._name_edit.setPlaceholderText("e.g. RED")
        trainer_row.addWidget(self._name_edit)
        trainer_row.addSpacing(20)
        trainer_row.addWidget(QLabel("Gender:"))
        self._gender_boy  = QRadioButton("Boy")
        self._gender_girl = QRadioButton("Girl")
        self._gender_boy.setChecked(True)
        self._gender_group = QButtonGroup()
        self._gender_group.addButton(self._gender_boy,  0)
        self._gender_group.addButton(self._gender_girl, 1)
        trainer_row.addWidget(self._gender_boy)
        trainer_row.addWidget(self._gender_girl)
        trainer_row.addStretch()
        vl.addLayout(trainer_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Format:"))
        self._fmt_rng = QRadioButton("EonTimer / RNG")
        self._fmt_tas = QRadioButton("TAS / Frame Advance")
        self._fmt_rng.setChecked(True)
        self._fmt_group = QButtonGroup()
        self._fmt_group.addButton(self._fmt_rng, 0)
        self._fmt_group.addButton(self._fmt_tas, 1)
        fmt_row.addWidget(self._fmt_rng)
        fmt_row.addWidget(self._fmt_tas)
        fmt_row.addStretch()
        vl.addLayout(fmt_row)

        gen_btn = QPushButton("Generate Instructions")
        gen_btn.setFixedHeight(36)
        gen_btn.clicked.connect(self._do_rng_instructions)
        vl.addWidget(gen_btn)

        self._rng_output = QTextEdit()
        self._rng_output.setReadOnly(True)
        self._rng_output.setFont(QFont("Menlo", 11))
        self._rng_output.setPlaceholderText("Instructions will appear here…")
        vl.addWidget(self._rng_output, stretch=1)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(self._rng_output.toPlainText())
        )
        vl.addWidget(copy_btn)
        return w

    def _build_inject_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(12, 12, 12, 12)
        vl.setSpacing(10)

        note = QLabel(
            "Provide a .sav from the start of the game — create a new save and "
            "reach the first save point. The tool patches TID and SID, then "
            "recalculates the block checksums. Trainer name and gender are preserved."
        )
        note.setWordWrap(True)
        vl.addWidget(note)

        in_row = QHBoxLayout()
        in_row.addWidget(QLabel("Input save (.sav):"))
        self._in_path = QLineEdit()
        self._in_path.setPlaceholderText("Browse…")
        self._in_path.setReadOnly(True)
        in_row.addWidget(self._in_path, stretch=1)
        in_browse = QPushButton("Browse…")
        in_browse.clicked.connect(self._browse_input)
        in_row.addWidget(in_browse)
        vl.addLayout(in_row)

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Output save (.sav):"))
        self._out_path = QLineEdit()
        self._out_path.setPlaceholderText("Browse…")
        self._out_path.setReadOnly(True)
        out_row.addWidget(self._out_path, stretch=1)
        out_browse = QPushButton("Browse…")
        out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(out_browse)
        vl.addLayout(out_row)

        gen_btn = QPushButton("Generate Patched Save File")
        gen_btn.setFixedHeight(36)
        gen_btn.clicked.connect(self._do_inject)
        vl.addWidget(gen_btn)
        vl.addStretch()
        return w

    def _current_game(self) -> str | None:
        text = self._game_combo.currentText()
        return text if text in GAME_CONFIGS else None

    def _on_settings_changed(self):
        self._refresh_groups()

    def _refresh_groups(self):
        lead = "Male" if self._lead_male.isChecked() else "Female"
        ratio = self._ratio_combo.currentText()

        self._ratio_combo.setEnabled(lead == "Female")

        groups = shiny_groups(lead, ratio)
        self._group_data = groups

        prev_idx = self._group_btn_group.checkedId()
        selected = prev_idx if 0 <= prev_idx < len(groups) else 0

        for r in self._group_radios:
            self._group_btn_group.removeButton(r)
            self._groups_layout.removeWidget(r)
            r.deleteLater()
        self._group_radios.clear()

        for i, g in enumerate(groups):
            natures_str = ", ".join(g["natures"])
            label = f"Group {i+1}  ({len(g['natures'])} natures)  —  {natures_str}"
            rb = QRadioButton(label)
            rb.setChecked(i == selected)
            rb.toggled.connect(self._refresh_tid_sid)
            self._group_btn_group.addButton(rb, i)
            self._groups_layout.addWidget(rb)
            self._group_radios.append(rb)

        self._refresh_tid_sid()

    def _refresh_tid_sid(self):
        idx = self._group_btn_group.checkedId()
        if idx < 0 or idx >= len(self._group_data):
            self._tid_label.setText("TID: —")
            self._sid_label.setText("SID: —")
            self._tsv_label.setText("TSV: —")
            return
        group = self._group_data[idx]
        tsv_val = group["tsv_value"]
        pref = self._tid_spin.value() if self._tid_spin.value() > 0 else None
        tid, sid = find_tid_sid(tsv_val, pref)
        self._tid_label.setText(f"TID: {tid:05d}")
        self._sid_label.setText(f"SID: {sid:05d}")
        self._tsv_label.setText(f"TSV: {tsv_val}")

    def _current_tid_sid(self) -> tuple[int, int] | None:
        idx = self._group_btn_group.checkedId()
        if idx < 0 or idx >= len(self._group_data):
            return None
        group = self._group_data[idx]
        pref = self._tid_spin.value() if self._tid_spin.value() > 0 else None
        return find_tid_sid(group["tsv_value"], pref)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select save file", "", "Save files (*.sav *.SAV);;All files (*)"
        )
        if path:
            self._in_path.setText(path)
            if not self._out_path.text():
                base, ext = os.path.splitext(path)
                self._out_path.setText(f"{base}_cutecharm{ext}")

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save output file", "", "Save files (*.sav);;All files (*)"
        )
        if path:
            self._out_path.setText(path)

    def _do_inject(self):
        in_path = self._in_path.text().strip()
        out_path = self._out_path.text().strip()
        if not in_path:
            QMessageBox.warning(self, "No input", "Please select an input save file.")
            return
        if not out_path:
            QMessageBox.warning(self, "No output", "Please select an output path.")
            return

        game = self._current_game()
        if game is None:
            QMessageBox.warning(self, "No game selected", "Please select your game.")
            return

        result = self._current_tid_sid()
        if result is None:
            QMessageBox.warning(self, "No group selected", "Select a shiny group first.")
            return
        tid, sid = result

        try:
            with open(in_path, "rb") as f:
                original = f.read()
        except OSError as e:
            QMessageBox.critical(self, "Read error", str(e))
            return

        cfg = GAME_CONFIGS[game]
        existing_gender = original[cfg.trainer1_offset + 0x18]

        try:
            patched = patch_save(original, game, "", existing_gender, tid, sid, keep_name=True)
        except Exception as e:
            QMessageBox.critical(self, "Patch error", str(e))
            return

        try:
            with open(out_path, "wb") as f:
                f.write(patched)
        except OSError as e:
            QMessageBox.critical(self, "Write error", str(e))
            return

        QMessageBox.information(
            self,
            "Done",
            f"Saved to:\n{out_path}\n\n"
            f"TID: {tid:05d}   SID: {sid:05d}\n"
            f"Trainer name and gender preserved from original save.",
        )

    def _do_rng_instructions(self):
        errors = validate_name(self._name_edit.text().strip())
        if errors:
            QMessageBox.warning(self, "Invalid input", "\n".join(errors))
            return

        game = self._current_game()
        if game is None:
            QMessageBox.warning(self, "No game selected", "Please select your game.")
            return

        result = self._current_tid_sid()
        if result is None:
            QMessageBox.warning(self, "No group selected", "Select a shiny group first.")
            return
        tid, sid = result

        name   = self._name_edit.text().strip()
        gender = "Boy" if self._gender_boy.isChecked() else "Girl"
        seeds  = find_seed_for_tid_sid(tid, sid)

        if self._fmt_tas.isChecked():
            text = build_tas_instructions(game, name, gender, tid, sid, seeds)
        else:
            text = build_instructions(game, name, gender, tid, sid, seeds)
        self._rng_output.setPlainText(text)

    def _show_info(self):
        dlg = InfoDialog(self)
        dlg.exec()
