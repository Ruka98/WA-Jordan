# license_page.py
# A startup license dialog for WA+ Water Accounting Tool
#
# Usage:
#   from license_page import LicenseDialog
#   dlg = LicenseDialog("LICENSE.txt")  # relative to app root (works with PyInstaller too)
#   if dlg.exec_() != LicenseDialog.Accepted:
#       sys.exit(0)
#
# Notes:
# - Reads the license text from a separate file (no hardcoding).
# - Styled to match the app (colors, rounded buttons).
# - Provides Accept / Decline actions; Accept only enabled after the user scrolls to the bottom.
# - No external links shown or opened.

import os
import sys
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton, QLabel, QMessageBox, QSizePolicy
)

def resource_path(relative_path: str) -> str:
    """
    Resolve a resource path that works in dev and in a PyInstaller bundle.
    It prefers the PyInstaller extraction dir (_MEIPASS) when frozen.
    """
    # Normalize just in case a Path was passed
    rel = str(relative_path).strip().lstrip("\\/")

    base_path = None
    # When frozen by PyInstaller
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", None)

    if not base_path:
        base_path = os.path.abspath(".")

    candidate = os.path.join(base_path, rel)
    if os.path.exists(candidate):
        return candidate

    # Fallback to current working directory (useful during dev runs)
    fallback = os.path.abspath(os.path.join(".", rel))
    return fallback

class LicenseDialog(QDialog):
    def __init__(self, license_file: str = "LICENSE.txt"):
        super().__init__()
        self.setWindowTitle("License Agreement — WA+ Water Accounting Tool")
        self.setModal(True)
        self.resize(720, 520)

        # Light theme styling to match the app
        self.setStyleSheet("""
            QDialog {
                background: #f5f5f5;
            }
            QLabel {
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QTextBrowser {
                background: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 10px;
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f6699;
            }
            QPushButton#secondary {
                background-color: white;
                color: #EF5350;
                border: 1px solid #EF5350;
            }
            QPushButton#secondary:hover {
                background-color: #FFEBEE;
            }
            #title {
                font-size: 20px;
                font-weight: bold;
                color: #4FC3F7;
            }
            #subtitle {
                color: #666666;
                font-size: 12px;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        # Title
        title = QLabel("Please review and accept the license to continue")
        title.setObjectName("title")
        main.addWidget(title)

        # Informative subtitle (no links)
        subtitle = QLabel("License: Creative Commons Attribution 4.0 International (CC BY 4.0)")
        subtitle.setObjectName("subtitle")
        main.addWidget(subtitle)

        # License text area (read from file) - no external links
        self.viewer = QTextBrowser()
        self.viewer.setReadOnly(True)
        self.viewer.setOpenExternalLinks(False)  # ensure no links are opened
        self.viewer.setOpenLinks(False)          # block link navigation entirely
        self.viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main.addWidget(self.viewer, 1)

        # Load content (read-only)
        resolved = resource_path(license_file)
        txt = self._read_text_file(resolved)

        # Render the file text plainly (no anchor rendering)
        # Using <pre> for layout stability; no hyperlinks and minimal HTML
        html = f"""
            <html>
              <body style="background:#ffffff; margin:0; padding:0;">
                <pre style="white-space: pre-wrap; margin:0; padding:0 0 8px 0;
                            font-family: 'Segoe UI', Arial, sans-serif; font-size:13px; color:#333333;">{self._escape_html(txt)}
                </pre>
              </body>
            </html>
        """
        self.viewer.setHtml(html)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.decline_btn = QPushButton("Decline")
        self.decline_btn.setObjectName("secondary")
        self.decline_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.decline_btn)

        self.accept_btn = QPushButton("Accept")
        self.accept_btn.setEnabled(False)  # enabled after scroll to bottom
        self.accept_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.accept_btn)
        main.addLayout(btn_row)

        # Enable "Accept" only after user scrolls to bottom
        self.viewer.verticalScrollBar().valueChanged.connect(self._maybe_enable_accept)
        self._maybe_enable_accept()  # handle short texts immediately

    def _read_text_file(self, path: str) -> str:
        """Read a text file safely with UTF-8 first, then fall back to system encodings."""
        if not path or not os.path.exists(path):
            return "LICENSE.txt not found. Please include the license file in your application directory."
        # Try UTF-8 first
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            # Fallback to common Windows encoding if needed
            try:
                with open(path, "r", encoding="cp1252", errors="replace") as f:
                    return f.read()
            except Exception as e2:
                return f"Error reading license file: {e2}"

    def _escape_html(self, s: str) -> str:
        """Escape minimal HTML to avoid accidental markup from license text."""
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
        )

    def _maybe_enable_accept(self, *_):
        sb = self.viewer.verticalScrollBar()
        # If there's no scrollbar or already at bottom, enable
        if not sb.maximum() or sb.value() >= sb.maximum() - 4:
            self.accept_btn.setEnabled(True)
        else:
            self.accept_btn.setEnabled(False)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dlg = LicenseDialog("LICENSE.txt")
    if dlg.exec_() == QDialog.Accepted:
        QMessageBox.information(None, "License", "Accepted. Continue to app...")
        sys.exit(0)
    else:
        QMessageBox.information(None, "License", "Declined. Closing app.")
        sys.exit(1)
