import sys
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLabel, QPushButton, QFileDialog, QProgressBar,
    QLineEdit, QHBoxLayout, QScrollArea, QMessageBox, QTextEdit, QStyleFactory
)
from PySide6.QtCore import Qt, QUrl, QTimer, Signal, QObject, QSettings
from PySide6.QtGui import QDesktopServices, QFontDatabase, QFont


class LogEmitter(QObject):
    log_signal = Signal(str)


class JobViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.job_data = []
        self.filtered_data = []
        self.current_index = -1
        self.log_emitter = LogEmitter()
        self.log_emitter.log_signal.connect(self.handle_log)

        # Load font size from settings or set default
        settings = QSettings("JobViewerApp", "FontSettings")
        self.font_size = int(settings.value("font_size", 10))
        self.fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.fixed_font.setPointSize(self.font_size)

        self.init_ui()
        self.apply_dark_theme()
        self.setWindowState(Qt.WindowState.WindowMaximized)

    def init_ui(self):
        self.setWindowTitle("Job Offer Viewer")
        self.setMinimumSize(800, 600)
        QApplication.setStyle(QStyleFactory.create('Fusion'))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        top_controls_layout = QHBoxLayout()

        file_layout = QHBoxLayout()
        self.btn_load = QPushButton("📂 Load JSON File")
        self.btn_load.clicked.connect(self.load_json)
        file_layout.addWidget(self.btn_load)
        top_controls_layout.addLayout(file_layout)

        search_layout = QVBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by keyword, company, etc.")
        self.search_field.textChanged.connect(self.apply_filter)
        search_layout.addWidget(self.search_field)
        top_controls_layout.addLayout(search_layout)

        font_controls_layout = QHBoxLayout()
        self.btn_decrease_font = QPushButton("A-")
        self.btn_decrease_font.clicked.connect(self.decrease_font_size)
        self.btn_increase_font = QPushButton("A+")
        self.btn_increase_font.clicked.connect(self.increase_font_size)
        self.lbl_font_size = QLabel(f"Font: {self.font_size}pt")
        font_controls_layout.addWidget(self.btn_decrease_font)
        font_controls_layout.addWidget(self.lbl_font_size)
        font_controls_layout.addWidget(self.btn_increase_font)
        top_controls_layout.addLayout(font_controls_layout)

        layout.addLayout(top_controls_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.job_display = QWidget()
        self.job_layout = QVBoxLayout(self.job_display)

        self.placeholder = QLabel("Please load a JSON file to view job offers")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setFont(self.fixed_font)
        self.job_layout.addWidget(self.placeholder)

        self.lbl_title = QLabel()
        self.lbl_title.setFont(self.fixed_font)
        self.lbl_company = QLabel()
        self.lbl_company.setFont(self.fixed_font)
        self.lbl_salary = QLabel()
        self.lbl_salary.setFont(self.fixed_font)

        self.txt_description = QTextEdit()
        self.txt_description.setReadOnly(True)
        self.txt_description.setFont(self.fixed_font)

        self.btn_apply = QPushButton("Apply Now")
        self.btn_apply.clicked.connect(self.open_job_link)

        for widget in [self.lbl_title, self.lbl_company, self.lbl_salary,
                       self.txt_description, self.btn_apply]:
            widget.setVisible(False)
            self.job_layout.addWidget(widget)

        scroll.setWidget(self.job_display)
        layout.addWidget(scroll)

        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Previous")
        self.btn_next = QPushButton("Next ▶")
        self.btn_prev.clicked.connect(self.prev_job)
        self.btn_next.clicked.connect(self.next_job)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        layout.addLayout(nav_layout)

        self.progress = QProgressBar()
        self.progress.setFormat("%v/%m (%p%)")
        layout.addWidget(self.progress)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setMaximumHeight(100)
        self.log_viewer.setFont(self.fixed_font)
        layout.addWidget(self.log_viewer)

        self.toggle_navigation(False)

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

    def apply_dark_theme(self):
        dark_palette = self.palette()
        dark_palette.setColor(dark_palette.ColorRole.Window, Qt.GlobalColor.darkGray)
        dark_palette.setColor(dark_palette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(dark_palette.ColorRole.Base, Qt.GlobalColor.black)
        dark_palette.setColor(dark_palette.ColorRole.AlternateBase, Qt.GlobalColor.darkGray)
        dark_palette.setColor(dark_palette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(dark_palette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(dark_palette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(dark_palette.ColorRole.Button, Qt.GlobalColor.darkGray)
        dark_palette.setColor(dark_palette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(dark_palette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(dark_palette.ColorRole.Highlight, Qt.GlobalColor.blue)
        dark_palette.setColor(dark_palette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(dark_palette)

    def log(self, message):
        self.log_emitter.log_signal.emit(message)

    def handle_log(self, message):
        self.log_viewer.append(message)
        self.log_viewer.verticalScrollBar().setValue(
            self.log_viewer.verticalScrollBar().maximum()
        )

    def load_json(self):
        try:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Open JSON File", "", "JSON Files (*.json)"
            )
            if filepath:
                QTimer.singleShot(0, lambda: self._load_json_file(filepath))
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def _load_json_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list) or not data:
                raise ValueError("JSON file must contain a non-empty array of job objects")
            self.job_data = data
            self.filtered_data = data.copy()
            self.current_index = 0
            QTimer.singleShot(0, self.update_display)
            self.placeholder.setVisible(False)
            for widget in [self.lbl_title, self.lbl_company, self.lbl_salary,
                           self.txt_description, self.btn_apply]:
                widget.setVisible(True)
            self.log(f"✅ Loaded {len(data)} jobs from {filepath}")
        except Exception as e:
            self.log(f"❌ Failed to load JSON: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def apply_filter(self):
        if hasattr(self, '_filter_timer'):
            self._filter_timer.stop()
        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(self._apply_filter_actual)
        self._filter_timer.start(300)

    def _apply_filter_actual(self):
        search_text = self.search_field.text().lower()
        if not search_text:
            self.filtered_data = self.job_data.copy()
        else:
            self.filtered_data = [
                job for job in self.job_data
                if any(search_text in job.get(field, '').lower()
                       for field in ['JobOfferTitle', 'CompanyName', 'Description', 'SalaryOrBudgetOffered'])
            ]
        self.current_index = 0 if self.filtered_data else -1
        self.toggle_navigation(bool(self.filtered_data))
        self.update_display()
        self.log(f"🔍 Applied filter → {len(self.filtered_data)} matches")

    def update_display(self):
        if not self.filtered_data or self.current_index < 0:
            return
        job = self.filtered_data[self.current_index]
        self.lbl_title.setText(job.get('JobOfferTitle', 'No title'))
        self.lbl_company.setText(f"Company: {job.get('CompanyName', 'Not specified')}")
        salary = job.get('SalaryOrBudgetOffered')
        self.lbl_salary.setText(f"Salary/Budget: {salary}") if salary else self.lbl_salary.setVisible(False)
        self.lbl_salary.setVisible(bool(salary))
        desc = job.get('Description', 'No description available')
        self.txt_description.setHtml(f"<pre>{desc}</pre>")
        self.btn_apply.setVisible('Link' in job and job['Link'])
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
            self.log(f"➡ Job {self.current_index + 1}/{len(self.filtered_data)}")

    def prev_job(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()
            self.log(f"⬅ Job {self.current_index + 1}/{len(self.filtered_data)}")

    def open_job_link(self):
        if self.filtered_data and 0 <= self.current_index < len(self.filtered_data):
            job = self.filtered_data[self.current_index]
            if 'Link' in job and job['Link']:
                QDesktopServices.openUrl(QUrl(job['Link']))
                self.log(f"🌐 Opened: {job['Link']}")

    def update_fonts(self):
        self.fixed_font.setPointSize(self.font_size)
        widgets = [
            self.placeholder, self.lbl_title, self.lbl_company,
            self.lbl_salary, self.txt_description, self.btn_apply,
            self.btn_prev, self.btn_next, self.search_field,
            self.btn_load, self.log_viewer, self.lbl_font_size
        ]
        for widget in widgets:
            widget.setFont(self.fixed_font)
        self.lbl_font_size.setText(f"Font: {self.font_size}pt")
        self.save_settings()

    def increase_font_size(self):
        if self.font_size < 24:
            self.font_size += 1
            self.update_fonts()
            self.log(f"🔍 Increased font size to {self.font_size}pt")

    def decrease_font_size(self):
        if self.font_size > 8:
            self.font_size -= 1
            self.update_fonts()
            self.log(f"🔍 Decreased font size to {self.font_size}pt")

    def save_settings(self):
        settings = QSettings("JobViewerApp", "FontSettings")
        settings.setValue("font_size", self.font_size)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    window = JobViewerApp()
    window.show()
    sys.exit(app.exec())
