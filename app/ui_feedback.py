"""
Shared UI feedback helpers (success/error/warn/loading) for consistent UX.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QWidget


_DIALOG_STYLE = """
QMessageBox, QDialog {
    background-color: white !important;
    background: white !important;
}
QMessageBox QLabel {
    color: #111827 !important;
    background: transparent !important;
    font-size: 11pt;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
}
QPushButton {
    background-color: #f8fafc !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 10pt;
    font-weight: 600;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #f1f5f9 !important;
    border-color: #cbd5e1;
    color: #0f172a !important;
}
QPushButton:pressed {
    background-color: #e2e8f0 !important;
}
"""


def apply_dialog_style(box: QWidget) -> None:
    # Global dialog styles can reset layout-derived minimum size hints until a later
    # resize event — callers often see a one-frame "tiny" dialog before it expands.
    prev_min = QSize(box.minimumSize())
    box.setStyleSheet(_DIALOG_STYLE)
    
    if isinstance(box, QMessageBox):
        # QMessageBox needs explicit width for consistent text wrapping in our premium style.
        # 440px provides a comfortable line length for clinical explanations.
        box.setMinimumWidth(440)
        box.setMinimumHeight(180) # Ensure enough height for icon + text + buttons
        
        # Ensure the layout respects the new minimum width immediately
        lay = box.layout()
        if lay:
            lay.activate()
            # Add some breathing room around the edges
            lay.setContentsMargins(20, 20, 20, 20)
            if hasattr(lay, "setSpacing"):
                lay.setSpacing(15)

        for label in box.findChildren(QLabel):
            # Target main text labels (qt_msgbox_label, qt_msgbox_informativelabel)
            obj_name = label.objectName()
            is_text = label.text() and (not label.pixmap())
            
            if is_text or obj_name in ("qt_msgbox_label", "qt_msgbox_informativelabel"):
                label.setWordWrap(True)
                # Ensure text labels have enough space and correct font
                label.setStyleSheet("padding: 5px 0px; font-size: 11pt; background: transparent;")
            elif label.pixmap() or "icon" in obj_name.lower():
                # Ensure the icon isn't squashed and has some margin
                label.setStyleSheet("padding: 0px; margin-right: 15px; background: transparent;")
    else:
        # For standard QDialogs (like Comparison or Patient Overview), we avoid 
        # setFixedWidth so the window can respect its own size/minimum-size logic.
        if prev_min.width() > 0 or prev_min.height() > 0:
            box.setMinimumSize(
                max(prev_min.width(), box.minimumWidth()),
                max(prev_min.height(), box.minimumHeight()),
            )
        elif box.minimumWidth() < 400:
            box.setMinimumWidth(400)


def show_success(parent: QWidget, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(message)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    apply_dialog_style(box)  # apply AFTER setText so the label already exists
    box.exec()


def show_error(parent: QWidget, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    apply_dialog_style(box)
    box.exec()


def show_warning(parent: QWidget, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(message)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    apply_dialog_style(box)
    box.exec()


def confirm(
    parent: QWidget,
    title: str,
    message: str,
    *,
    informative_text: str | None = None,
    yes_text: str = "Yes",
    no_text: str = "No",
) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(message)
    if informative_text:
        box.setInformativeText(informative_text)
    yes = box.addButton(yes_text, QMessageBox.ButtonRole.AcceptRole)
    no = box.addButton(no_text, QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(no)
    apply_dialog_style(box)  # apply AFTER addButton so all labels exist
    box.exec()
    return box.clickedButton() == yes


@contextmanager
def loading_state(
    buttons: Iterable[QPushButton],
    *,
    loading_text: str = "Processing…",
):
    btns = [b for b in buttons if isinstance(b, QPushButton)]
    prior = [(b, b.text(), b.isEnabled(), b.cursor()) for b in btns]
    for b in btns:
        b.setEnabled(False)
        if loading_text:
            b.setText(loading_text)
        b.setCursor(Qt.CursorShape.BusyCursor)
    try:
        yield
    finally:
        for b, text, enabled, cursor in prior:
            b.setText(text)
            b.setEnabled(enabled)
            b.setCursor(cursor)  # restore the original cursor, not a hardcoded arrow