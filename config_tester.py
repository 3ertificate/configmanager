# config_tester.py
import asyncio
import aiohttp
import time
from dataclasses import dataclass
from typing import List, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem, QProgressBar,
                           QLabel, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from config_processor import ConfigData
from PyQt6.QtCore import pyqtSignal

@dataclass
class TestResult:
    config: ConfigData
    delay: float
    success: bool
    error: Optional[str] = None

class ConfigTester(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(TestResult)
    finished = pyqtSignal()

    def __init__(self, configs: List[ConfigData], max_retries: int = 3):
        super().__init__()
        self.configs = configs
        self.max_retries = max_retries
        self.stop_flag = False

    async def test_single_config(self, config: ConfigData) -> TestResult:
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # تنظیم پروکسی بر اساس نوع کانفیگ
                    proxy_url = self._get_proxy_url(config)
                    
                    # تست اتصال با استفاده از پروکسی
                    async with session.get('http://www.google.com', 
                                        proxy=proxy_url,
                                        timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            delay = (time.time() - start_time) * 1000  # تبدیل به میلی‌ثانیه
                            return TestResult(config=config, delay=delay, success=True)
            
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    return TestResult(
                        config=config,
                        delay=float('inf'),
                        success=False,
                        error="Timeout"
                    )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return TestResult(
                        config=config,
                        delay=float('inf'),
                        success=False,
                        error=str(e)
                    )
            
            if self.stop_flag:
                return TestResult(
                    config=config,
                    delay=float('inf'),
                    success=False,
                    error="Cancelled"
                )
            
            # انتظار کوتاه قبل از تلاش مجدد
            await asyncio.sleep(1)
        
        return TestResult(
            config=config,
            delay=float('inf'),
            success=False,
            error="Max retries reached"
        )

    def _get_proxy_url(self, config: ConfigData) -> str:
        # ساخت URL پروکسی بر اساس نوع کانفیگ
        if config.type == "trojan":
            return f"trojan://{config.raw_config['password']}@{config.server}:{config.port}"
        elif config.type == "vmess":
            # ساخت URL برای VMess نیاز به پارامترهای بیشتری دارد
            return f"vmess://{config.server}:{config.port}"
        elif config.type == "vless":
            return f"vless://{config.raw_config['uuid']}@{config.server}:{config.port}"
        # می‌توان انواع دیگر را هم اضافه کرد
        return ""

    async def run_tests(self):
        total = len(self.configs)
        completed = 0
        
        # تست همزمان کانفیگ‌ها
        tasks = []
        for config in self.configs:
            if self.stop_flag:
                break
            
            task = asyncio.create_task(self.test_single_config(config))
            tasks.append(task)
            
            # محدود کردن تعداد تست‌های همزمان
            if len(tasks) >= 5:
                done, tasks = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    result = await task
                    self.result.emit(result)
                    completed += 1
                    self.progress.emit(int((completed / total) * 100))
        
        # انتظار برای اتمام تست‌های باقی‌مانده
        if tasks:
            done, _ = await asyncio.wait(tasks)
            for task in done:
                result = await task
                self.result.emit(result)
                completed += 1
                self.progress.emit(int((completed / total) * 100))

    def run(self):
        asyncio.run(self.run_tests())
        self.finished.emit()

    def stop(self):
        self.stop_flag = True

class TestTab(QWidget):
    results_updated = pyqtSignal(list)  # اضافه کردن این خط
    def __init__(self, parent=None):
        super().__init__(parent)
        self.test_results: List[TestResult] = []
        self.max_configs = 50
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # تنظیمات تست
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("حداکثر تعداد کانفیگ:"))
        self.max_configs_spin = QSpinBox()
        self.max_configs_spin.setRange(1, 100)
        self.max_configs_spin.setValue(self.max_configs)
        self.max_configs_spin.valueChanged.connect(self._update_max_configs)
        settings_layout.addWidget(self.max_configs_spin)
        settings_layout.addStretch()
        layout.addLayout(settings_layout)
        
        # جدول نتایج
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(
            ["نام", "نوع", "سرور", "تاخیر (ms)", "وضعیت"]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)
        
        # نوار پیشرفت
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # دکمه‌های کنترل
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("شروع تست")
        self.start_button.clicked.connect(self.start_tests)
        self.stop_button = QPushButton("توقف")
        self.stop_button.clicked.connect(self.stop_tests)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        layout.addLayout(buttons_layout)

    def _update_max_configs(self, value):
        self.max_configs = value

    def set_configs(self, configs: List[ConfigData]):
        self.configs = configs[:self.max_configs]
        self.test_results.clear()
        self.results_table.setRowCount(0)

    def start_tests(self):
        if not hasattr(self, 'configs') or not self.configs:
            QMessageBox.warning(self, "خطا", "هیچ کانفیگی برای تست وجود ندارد")
            return
        
        self.test_results.clear()
        self.results_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        self.tester = ConfigTester(self.configs)
        self.tester.progress.connect(self._update_progress)
        self.tester.result.connect(self._add_result)
        self.tester.finished.connect(self._testing_finished)
        self.tester.start()

    def stop_tests(self):
        if hasattr(self, 'tester'):
            self.tester.stop()
            self.stop_button.setEnabled(False)

    def _update_progress(self, value):
        self.progress_bar.setValue(value)

    def _add_result(self, result: TestResult):
        if not result.success:
            return
        
        self.test_results.append(result)
        self._update_results_table()

    def _update_results_table(self):
        # مرتب‌سازی نتایج بر اساس تاخیر
        sorted_results = sorted(
            self.test_results,
            key=lambda x: x.delay
        )
        
        self.results_table.setRowCount(len(sorted_results))
        for i, result in enumerate(sorted_results):
            self.results_table.setItem(i, 0, QTableWidgetItem(result.config.name))
            self.results_table.setItem(i, 1, QTableWidgetItem(result.config.type))
            self.results_table.setItem(i, 2, QTableWidgetItem(result.config.server))
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{result.delay:.1f}"))
            
            status = "موفق" if result.success else f"ناموفق: {result.error}"
            self.results_table.setItem(i, 4, QTableWidgetItem(status))

    def _testing_finished(self):
        self.progress_bar.hide()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        QMessageBox.information(
            self,
            "اتمام تست",
            f"تست {len(self.test_results)} کانفیگ با موفقیت انجام شد"
        )
