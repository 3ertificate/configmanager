# main.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

class ConfigManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مدیریت کانفیگ‌های شبکه")
        self.setMinimumSize(800, 600)
        
        # ایجاد ویجت مرکزی و لایه اصلی
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # ایجاد تب‌ها
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.tabs)
        
        # اضافه کردن تب‌های اصلی
        self.subscription_tab = SubscriptionTab()
        self.configs_tab = ConfigsTab()
        self.report_tab = ReportTab()
        
        self.tabs.addTab(self.subscription_tab, "مدیریت لینک‌ها")
        self.tabs.addTab(self.configs_tab, "کانفیگ‌ها")
        self.tabs.addTab(self.report_tab, "گزارش‌ها")

class SubscriptionTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        # TODO: اضافه کردن المان‌های مربوط به مدیریت لینک‌ها

class ConfigsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        # TODO: اضافه کردن المان‌های مربوط به نمایش و مدیریت کانفیگ‌ها

class ReportTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        # TODO: اضافه کردن المان‌های مربوط به گزارش‌ها

def main():
    app = QApplication(sys.argv)
    
    # تنظیم فونت و استایل برای پشتیبانی از فارسی
    font = app.font()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    
    window = ConfigManagerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
