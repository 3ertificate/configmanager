# subscription_manager.py
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLineEdit, QListWidget, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import requests

class LinkDownloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str, str)  # Success, Message, Content

    def __init__(self, link):
        super().__init__()
        self.link = link

    def run(self):
        try:
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Download the content
            response = requests.get(self.link, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                # Try to decode if it's base64 encoded
                try:
                    decoded_content = base64.b64decode(content).decode('utf-8')
                    self.finished.emit(True, "دانلود با موفقیت انجام شد", decoded_content)
                except:
                    # If not base64, use the content as is
                    self.finished.emit(True, "دانلود با موفقیت انجام شد", content)
            else:
                self.finished.emit(False, f"خطا در دانلود: {response.status_code}", "")
                
        except requests.exceptions.Timeout:
            self.finished.emit(False, "خطا: زمان دانلود به پایان رسید", "")
        except requests.exceptions.RequestException as e:
            self.finished.emit(False, f"خطا در دانلود: {str(e)}", "")
        except Exception as e:
            self.finished.emit(False, f"خطای غیرمنتظره: {str(e)}", "")

class SubscriptionManager:
    def __init__(self):
        self.config_path = Path.home() / '.config_manager'
        self.config_path.mkdir(exist_ok=True)
        self.links_file = self.config_path / 'links.enc'
        self._init_encryption()
        self.links = self._load_links()

    def _init_encryption(self):
        try:
            salt = b'config_manager_salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(b'static_key'))
            self.cipher_suite = Fernet(key)
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            # Use a fallback encryption key if the above fails
            self.cipher_suite = Fernet(Fernet.generate_key())

    def _load_links(self):
        if not self.links_file.exists():
            return []
        try:
            encrypted_data = self.links_file.read_bytes()
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            print(f"Error loading links: {e}")
            return []

    def save_links(self):
        try:
            encrypted_data = self.cipher_suite.encrypt(json.dumps(self.links).encode())
            self.links_file.write_bytes(encrypted_data)
            return True
        except Exception as e:
            print(f"Error saving links: {e}")
            return False

    def add_link(self, link):
        if link not in self.links:
            self.links.append(link)
            return self.save_links()
        return False

    def remove_link(self, link):
        if link in self.links:
            self.links.remove(link)
            return self.save_links()
        return False

    def get_links(self):
        return self.links.copy()

class SubscriptionTab(QWidget):
    configs_updated = pyqtSignal(list)  # Signal for updating configs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.subscription_manager = SubscriptionManager()
        self._init_ui()
        self._load_saved_links()
        self.current_downloader = None

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # بخش افزودن لینک
        input_layout = QHBoxLayout()
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("لینک ساب‌اسکریپشن را وارد کنید...")
        self.add_button = QPushButton("افزودن")
        self.add_button.clicked.connect(self._add_link)
        
        input_layout.addWidget(self.link_input)
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)

        # لیست لینک‌ها
        self.links_list = QListWidget()
        self.links_list.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout.addWidget(self.links_list)

        # دکمه‌های مدیریت
        buttons_layout = QHBoxLayout()
        self.remove_button = QPushButton("حذف")
        self.remove_button.clicked.connect(self._remove_link)
        self.update_button = QPushButton("به‌روزرسانی")
        self.update_button.clicked.connect(self._update_links)
        
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addWidget(self.update_button)
        layout.addLayout(buttons_layout)

        # نوار پیشرفت
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

    def _load_saved_links(self):
        self.links_list.clear()
        for link in self.subscription_manager.get_links():
            self.links_list.addItem(link)

    def _add_link(self):
        link = self.link_input.text().strip()
        if not link:
            QMessageBox.warning(self, "خطا", "لطفاً یک لینک وارد کنید")
            return

        if self.subscription_manager.add_link(link):
            self.links_list.addItem(link)
            self.link_input.clear()
            QMessageBox.information(self, "موفق", "لینک با موفقیت اضافه شد")
        else:
            QMessageBox.warning(self, "خطا", "این لینک قبلاً اضافه شده است")

    def _remove_link(self):
        current_item = self.links_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "خطا", "لطفاً یک لینک را انتخاب کنید")
            return

        link = current_item.text()
        if self.subscription_manager.remove_link(link):
            self.links_list.takeItem(self.links_list.row(current_item))
            QMessageBox.information(self, "موفق", "لینک با موفقیت حذف شد")

    def _update_links(self):
        if self.links_list.count() == 0:
            QMessageBox.warning(self, "خطا", "هیچ لینکی برای به‌روزرسانی وجود ندارد")
            return

        self.progress_bar.show()
        self.update_button.setEnabled(False)
        
        current_item = self.links_list.currentItem()
        if not current_item:
            current_item = self.links_list.item(0)
        
        self.current_downloader = LinkDownloader(current_item.text())
        self.current_downloader.progress.connect(self._update_progress)
        self.current_downloader.finished.connect(self._download_finished)
        self.current_downloader.start()

    def _update_progress(self, value):
        self.progress_bar.setValue(value)

    def _download_finished(self, success, message, content):
        self.update_button.setEnabled(True)
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        
        if success:
            try:
                # تقسیم محتوا به خطوط جداگانه برای پردازش هر کانفیگ
                configs = [line.strip() for line in content.split('\n') if line.strip()]
                self.configs_updated.emit(configs)  # ارسال لیست کانفیگ‌ها
                QMessageBox.information(self, "موفق", f"{len(configs)} کانفیگ با موفقیت دریافت شد")
            except Exception as e:
                QMessageBox.warning(self, "خطا", f"خطا در پردازش داده‌ها: {str(e)}")
        else:
            QMessageBox.warning(self, "خطا", message)

        self.current_downloader = None

    def closeEvent(self, event):
        if self.current_downloader and self.current_downloader.isRunning():
            self.current_downloader.terminate()
        event.accept()
