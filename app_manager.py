# app_manager.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QStatusBar
from PyQt6.QtCore import Qt, pyqtSlot

from subscription_manager import SubscriptionTab
from config_processor import ConfigsTab
from config_tester import TestTab
from report_generator import ReportTab

class AppManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مدیریت کانفیگ‌های شبکه")
        self.setMinimumSize(800, 600)
        
        # ایجاد ویجت مرکزی
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # ایجاد نوار وضعیت
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # ایجاد تب‌ها
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        main_layout.addWidget(self.tabs)
        
        # ایجاد و اضافه کردن تب‌ها
        self.subscription_tab = SubscriptionTab()
        self.configs_tab = ConfigsTab()
        self.test_tab = TestTab()
        self.report_tab = ReportTab()
        
        self.tabs.addTab(self.subscription_tab, "مدیریت لینک‌ها")
        self.tabs.addTab(self.configs_tab, "کانفیگ‌ها")
        self.tabs.addTab(self.test_tab, "تست")
        self.tabs.addTab(self.report_tab, "گزارش‌ها")
        
        # اتصال سیگنال‌ها
        self._connect_signals()
    
def _connect_signals(self):
    # اتصال سیگنال‌های بین تب‌ها
    self.subscription_tab.configs_updated.connect(self.configs_tab.process_subscription_data)
    self.configs_tab.configs_filtered.connect(self.test_tab.set_configs)
    self.test_tab.results_updated.connect(self.report_tab.set_results)
    
    @pyqtSlot(list)
    def _handle_configs_update(self, configs):
        """پردازش کانفیگ‌های دریافتی از subscription و ارسال به تب کانفیگ‌ها"""
        if configs:
            self.configs_tab.process_subscription_data("\n".join(configs))
            self.status_bar.showMessage("کانفیگ‌ها با موفقیت به‌روزرسانی شدند", 5000)
        else:
            self.status_bar.showMessage("خطا در پردازش کانفیگ‌ها", 5000)
