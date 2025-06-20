import sys
import json
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QLineEdit,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QMessageBox,
    QTextEdit
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices


class JobViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.job_data = []
        self.filtered_data = []
        self.current_index = -1
        self.init_ui()
        self.set_styles()

    def set_styles(self):
        """Apply CSS styles for better visual appearance."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 14px;
                margin: 5px 0;
            }
            QLabel[objectName^="lbl_title"] {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
            QLabel[objectName^="lbl_company"] {
                font-size: 16px;
                color: #7f8c8d;
            }
            QLabel[objectName^="lbl_salary"] {
                font-size: 15px;
                color: #27ae60;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QFrame {
                background-color: white;
                padding: 10px;
                border-radius: 4px;
            }
            QProgressBar {
                text-align: center;
            }
        """)

    def init_ui(self):
        self.setWindowTitle("Job Offer Viewer")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 14px;
                margin: 5px 0;
            }
            QLabel[objectName^="lbl_title"] {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel[objectName^="lbl_company"] {
                font-size: 16px;
                color: #aaaaaa;
            }
            QLabel[objectName^="lbl_salary"] {
                font-size: 15px;
                color: #81c784;
                font-weight: bold;
            }
            QPushButton {
                background-color: #1e88e5;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #424242;
                color: #777777;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                padding: 8px;
                font-size: 14px;
                border: 1px solid #333;
                border-radius: 4px;
            }
            QFrame {
                background-color: #1e1e1e;
                padding: 10px;
                border-radius: 4px;
            }
            QScrollArea {
                background-color: #121212;
            }
            QProgressBar {
                background-color: #333;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #1e88e5;
            }
        """)
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # File Selection + Search
        file_layout = QHBoxLayout()
        self.btn_load = QPushButton("📂 Load JSON File")
        self.btn_load.clicked.connect(self.load_json)
        file_layout.addWidget(self.btn_load)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by keyword, company, etc.")
        self.search_field.textChanged.connect(self.apply_filter)
        file_layout.addWidget(self.search_field)
        layout.addLayout(file_layout)

        # Job Display Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.job_display = QWidget()
        self.job_display.setStyleSheet("background-color: #1e1e1e;")
        self.job_layout = QVBoxLayout(self.job_display)
        self.placeholder = QLabel("Please load a JSON file to view job offers")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("font-size: 16px; color: #666;")
        self.job_layout.addWidget(self.placeholder)

        self.lbl_title = QLabel()
        self.lbl_company = QLabel()
        self.lbl_salary = QLabel()
        self.lbl_description = QLabel()
        self.lbl_description.setWordWrap(True)
        self.btn_apply = QPushButton("Apply Now")
        self.btn_apply.clicked.connect(self.open_job_link)

        for widget in [self.lbl_title, self.lbl_company, self.lbl_salary,
                       self.lbl_description, self.btn_apply]:
            widget.setVisible(False)
            self.job_layout.addWidget(widget)

        scroll.setWidget(self.job_display)
        layout.addWidget(scroll)

        # Navigation
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Previous")
        self.btn_next = QPushButton("Next ▶")
        self.btn_prev.clicked.connect(self.prev_job)
        self.btn_next.clicked.connect(self.next_job)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        layout.addLayout(nav_layout)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setFormat("%v/%m (%p%)")
        layout.addWidget(self.progress)

        # Log Viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setFixedHeight(100)
        self.log_viewer.setStyleSheet("""
            background-color: #1e1e1e;  /* Un gris oscuro compatible con dark mode */
            color: #d4d4d4;            /* Gris claro para texto */
            font-family: Consolas, monospace;
            font-size: 12px;
        """)
        layout.addWidget(self.log_viewer)

        self.toggle_navigation(False)

    def log(self, message):
        """Log messages to the log viewer and console."""
        self.log_viewer.append(message)


    def load_json(self):
        try:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Open JSON File", "", "JSON Files (*.json)"
            )
            if filepath:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not isinstance(data, list):
                    raise ValueError("JSON file should contain an array of job objects")

                if not data:
                    raise ValueError("JSON file is empty")

                self.job_data = data
                self.filtered_data = data.copy()
                self.current_index = 0
                self.update_display()

                self.placeholder.setVisible(False)
                for widget in [self.lbl_title, self.lbl_company, self.lbl_salary,
                               self.lbl_description, self.btn_apply]:
                    widget.setVisible(True)

                self.statusBar().showMessage(f"Loaded {len(data)} jobs")
                self.log(f"✅ Loaded {len(data)} jobs from {filepath}")

        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Invalid JSON file format")
            self.log("❌ Failed to load JSON: Invalid JSON file format")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            self.log(f"❌ Failed to load JSON: {str(e)}")

    def apply_filter(self):
        search_text = self.search_field.text().lower()
        if not search_text:
            self.filtered_data = self.job_data.copy()
        else:
            self.filtered_data = [
                job for job in self.job_data
                if (search_text in job.get('JobOfferTitle', '').lower() or
                    search_text in job.get('CompanyName', '').lower() or
                    search_text in job.get('Description', '').lower() or
                    search_text in job.get('SalaryOrBudgetOffered', '').lower())
            ]

        self.current_index = 0 if self.filtered_data else -1
        self.toggle_navigation(len(self.filtered_data) > 0)
        self.update_display()
        self.log(f"🔍 Applied filter '{search_text}' → {len(self.filtered_data)} jobs matched")

    def update_display(self):
        if not self.filtered_data or self.current_index < 0:
            return

        job = self.filtered_data[self.current_index]
        self.lbl_title.setText(job.get('JobOfferTitle', 'No title'))
        self.lbl_company.setText(f"Company: {job.get('CompanyName', 'Not specified')}")
        if salary := job.get('SalaryOrBudgetOffered'):
            self.lbl_salary.setText(f"SalaryOrBudgetOffered: {salary}")
            self.lbl_salary.setVisible(True)
        else:
            self.lbl_salary.setVisible(False)
        self.lbl_description.setText(job.get('Description', 'No description available'))
        self.btn_apply.setVisible('Link' in job)
        self.progress.setMaximum(len(self.filtered_data))
        self.progress.setValue(self.current_index + 1)
        self.setWindowTitle(f"Job Offer Viewer ({self.current_index + 1}/{len(self.filtered_data)})")
        self.toggle_navigation(True)

    def toggle_navigation(self, enabled):
        self.btn_prev.setEnabled(enabled and self.current_index > 0)
        self.btn_next.setEnabled(enabled and self.current_index < len(self.filtered_data) - 1)

    def next_job(self):
        if self.current_index < len(self.filtered_data) - 1:
            self.current_index += 1
            self.update_display()
            self.toggle_navigation(True)
            self.log(f"➡ Moved to job {self.current_index + 1}/{len(self.filtered_data)}")

    def prev_job(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()
            self.toggle_navigation(True)
            self.log(f"⬅ Moved to job {self.current_index + 1}/{len(self.filtered_data)}")

    def open_job_link(self):
        if self.filtered_data and 0 <= self.current_index < len(self.filtered_data):
            job = self.filtered_data[self.current_index]
            if 'link' in job and job['link']:
                QDesktopServices.openUrl(QUrl(job['link']))
                self.log(f"🌐 Opened link: {job['link']}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JobViewerApp()
    window.show()
    sys.exit(app.exec())
