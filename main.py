# main.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import Qt

# Import local modules
from subscription_manager import SubscriptionTab
from config_processor import ConfigsTab
from config_tester import TestTab
from report_generator import ReportTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مدیریت کانفیگ‌های شبکه")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        main_layout.addWidget(self.tabs)
        
        # Create individual tabs
        self.subscription_tab = SubscriptionTab()
        self.configs_tab = ConfigsTab()
        self.test_tab = TestTab()
        self.report_tab = ReportTab()
        
        # Add tabs to tab widget
        self.tabs.addTab(self.subscription_tab, "مدیریت لینک‌ها")
        self.tabs.addTab(self.configs_tab, "کانفیگ‌ها")
        self.tabs.addTab(self.test_tab, "تست")
        self.tabs.addTab(self.report_tab, "گزارش‌ها")

def main():
    app = QApplication(sys.argv)
    
    # Set default font for Persian support
    font = app.font()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
