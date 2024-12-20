# config_processor.py
import json
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem, QComboBox, QLabel,
                           QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal

@dataclass
class ConfigData:
    type: str
    name: str
    server: str
    port: int
    raw_config: dict
    
    def to_json(self) -> dict:
        return {
            "type": self.type,
            "name": self.name,
            "server": self.server,
            "port": self.port,
            "raw_config": self.raw_config
        }

class ConfigParser(ABC):
    @abstractmethod
    def can_parse(self, config_str: str) -> bool:
        pass
    
    @abstractmethod
    def parse(self, config_str: str) -> Optional[ConfigData]:
        pass

class TrojanParser(ConfigParser):
    def can_parse(self, config_str: str) -> bool:
        try:
            return config_str.startswith('trojan://')
        except:
            return False
    
    def parse(self, config_str: str) -> Optional[ConfigData]:
        try:
            # حذف پیشوند پروتکل
            config_str = config_str.replace('trojan://', '')
            
            # جداسازی اجزای آدرس
            parts = config_str.split('@')
            if len(parts) != 2:
                return None
                
            password = parts[0]
            server_parts = parts[1].split(':')
            if len(server_parts) != 2:
                return None
                
            server, port = server_parts
            port = int(port)
            
            return ConfigData(
                type="trojan",
                name=f"Trojan-{server}",
                server=server,
                port=port,
                raw_config={
                    "password": password,
                    "server": server,
                    "port": port
                }
            )
        except:
            return None

class VmessParser(ConfigParser):
    def can_parse(self, config_str: str) -> bool:
        try:
            return config_str.startswith('vmess://')
        except:
            return False
    
    def parse(self, config_str: str) -> Optional[ConfigData]:
        try:
            # حذف پیشوند پروتکل و رمزگشایی Base64
            config_str = config_str.replace('vmess://', '')
            decoded = base64.b64decode(config_str).decode('utf-8')
            config = json.loads(decoded)
            
            return ConfigData(
                type="vmess",
                name=config.get('ps', f"Vmess-{config['add']}"),
                server=config['add'],
                port=int(config['port']),
                raw_config=config
            )
        except:
            return None

class VlessParser(ConfigParser):
    def can_parse(self, config_str: str) -> bool:
        try:
            return config_str.startswith('vless://')
        except:
            return False
    
    def parse(self, config_str: str) -> Optional[ConfigData]:
        try:
            # پیاده‌سازی پارسر VLESS
            # مشابه Trojan با پارامترهای اضافی
            config_str = config_str.replace('vless://', '')
            parts = config_str.split('@')
            if len(parts) != 2:
                return None
                
            uuid = parts[0]
            server_parts = parts[1].split('?')[0].split(':')
            if len(server_parts) != 2:
                return None
                
            server, port = server_parts
            port = int(port)
            
            return ConfigData(
                type="vless",
                name=f"Vless-{server}",
                server=server,
                port=port,
                raw_config={
                    "uuid": uuid,
                    "server": server,
                    "port": port
                }
            )
        except:
            return None

class ConfigProcessor:
    def __init__(self):
        self.parsers: List[ConfigParser] = [
            TrojanParser(),
            VmessParser(),
            VlessParser()
            # می‌توان پارسرهای دیگر را هم اضافه کرد
        ]
        self.configs: List[ConfigData] = []
    
def process_subscription_data(self, data: str) -> bool:
    try:
        # تلاش برای رمزگشایی base64 اگر محتوا کدگذاری شده باشد
        try:
            decoded_data = base64.b64decode(data).decode('utf-8')
        except:
            decoded_data = data
            
        # تقسیم به خطوط جداگانه و حذف خطوط خالی
        config_lines = [line.strip() for line in decoded_data.split('\n') if line.strip()]
        
        successful_configs = []
        for config_str in config_lines:
            config = self.config_processor.process_single_config(config_str)
            if config:
                successful_configs.append(config)
        
        if successful_configs:
            self._update_table(successful_configs)
            self.configs_filtered.emit(successful_configs)
            return True
        return False
    except Exception as e:
        print(f"Error processing subscription data: {e}")
        return False
    
    def process_single_config(self, config_str: str) -> Optional[ConfigData]:
        for parser in self.parsers:
            if parser.can_parse(config_str):
                return parser.parse(config_str)
        return None
    
    def save_configs(self, filename: str) -> bool:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json_data = [config.to_json() for config in self.configs]
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configs: {e}")
            return False

class ConfigsTab(QWidget):
    configs_filtered = pyqtSignal(list)  # اضافه کردن این خط
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_processor = ConfigProcessor()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # فیلترهای نوع کانفیگ
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("نوع کانفیگ:"))
        self.config_type_filter = QComboBox()
        self.config_type_filter.addItems(["همه", "trojan", "vmess", "vless"])
        self.config_type_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.config_type_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # جدول کانفیگ‌ها
        self.configs_table = QTableWidget()
        self.configs_table.setColumnCount(4)
        self.configs_table.setHorizontalHeaderLabels(["نام", "نوع", "سرور", "پورت"])
        self.configs_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.configs_table)
        
        # دکمه‌های مدیریت
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("ذخیره کانفیگ‌ها")
        self.save_button.clicked.connect(self._save_configs)
        buttons_layout.addWidget(self.save_button)
        layout.addLayout(buttons_layout)
    
    def process_subscription_data(self, data: str):
        configs = self.config_processor.process_subscription_data(data)
        self._update_table(configs)
        return len(configs) > 0
    
    def _update_table(self, configs: List[ConfigData]):
        self.configs_table.setRowCount(0)
        for config in configs:
            row = self.configs_table.rowCount()
            self.configs_table.insertRow(row)
            
            self.configs_table.setItem(row, 0, QTableWidgetItem(config.name))
            self.configs_table.setItem(row, 1, QTableWidgetItem(config.type))
            self.configs_table.setItem(row, 2, QTableWidgetItem(config.server))
            self.configs_table.setItem(row, 3, QTableWidgetItem(str(config.port)))
    
    def _apply_filters(self):
        selected_type = self.config_type_filter.currentText()
        if selected_type == "همه":
            self._update_table(self.config_processor.configs)
        else:
            filtered_configs = [
                config for config in self.config_processor.configs
                if config.type == selected_type
            ]
            self._update_table(filtered_configs)
    
    def _save_configs(self):
        if not self.config_processor.configs:
            QMessageBox.warning(self, "خطا", "هیچ کانفیگی برای ذخیره وجود ندارد")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره کانفیگ‌ها",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if filename:
            if self.config_processor.save_configs(filename):
                QMessageBox.information(self, "موفق", "کانفیگ‌ها با موفقیت ذخیره شدند")
            else:
                QMessageBox.warning(self, "خطا", "خطا در ذخیره‌سازی کانفیگ‌ها")
