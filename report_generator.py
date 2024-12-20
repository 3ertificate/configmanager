# report_generator.py
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import matplotlib.pyplot as plt
from fpdf import FPDF
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTextEdit, QFileDialog, QComboBox, QLabel,
                           QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt
from config_processor import ConfigData
from config_tester import TestResult

class ReportGenerator:
    def __init__(self):
        self.report_dir = Path.home() / '.config_manager' / 'reports'
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_csv(self, results: List[TestResult], filename: str) -> bool:
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # نوشتن هدر
                writer.writerow(['Name', 'Type', 'Server', 'Port', 'Delay (ms)', 'Status'])
                
                # نوشتن داده‌ها
                for result in results:
                    writer.writerow([
                        result.config.name,
                        result.config.type,
                        result.config.server,
                        result.config.port,
                        f"{result.delay:.1f}",
                        "Success" if result.success else f"Failed: {result.error}"
                    ])
            return True
        except Exception as e:
            print(f"Error generating CSV: {e}")
            return False

    def generate_pdf(self, results: List[TestResult], filename: str) -> bool:
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # تنظیم فونت و استایل
            pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
            pdf.set_font('DejaVu', '', 12)
            
            # عنوان گزارش
            pdf.cell(0, 10, 'Configuration Test Report', 0, 1, 'C')
            pdf.ln(10)
            
            # اطلاعات کلی
            total_configs = len(results)
            successful_configs = len([r for r in results if r.success])
            avg_delay = sum(r.delay for r in results if r.success) / successful_configs if successful_configs > 0 else 0
            
            pdf.cell(0, 10, f'Total Configs: {total_configs}', 0, 1)
            pdf.cell(0, 10, f'Successful Configs: {successful_configs}', 0, 1)
            pdf.cell(0, 10, f'Average Delay: {avg_delay:.1f} ms', 0, 1)
            pdf.ln(10)
            
            # جدول نتایج
            col_widths = [40, 30, 40, 20, 30, 30]
            headers = ['Name', 'Type', 'Server', 'Port', 'Delay', 'Status']
            
            # هدر جدول
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1)
            pdf.ln()
            
            # داده‌های جدول
            for result in results:
                pdf.cell(col_widths[0], 10, result.config.name[:20], 1)
                pdf.cell(col_widths[1], 10, result.config.type, 1)
                pdf.cell(col_widths[2], 10, result.config.server[:20], 1)
                pdf.cell(col_widths[3], 10, str(result.config.port), 1)
                pdf.cell(col_widths[4], 10, f"{result.delay:.1f}", 1)
                status = "Success" if result.success else "Failed"
                pdf.cell(col_widths[5], 10, status, 1)
                pdf.ln()
            
            # ذخیره فایل
            pdf.output(filename)
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False

    def generate_summary(self, results: List[TestResult]) -> Dict:
        total_configs = len(results)
        successful_configs = len([r for r in results if r.success])
        
        type_stats = {}
        for result in results:
            config_type = result.config.type
            if config_type not in type_stats:
                type_stats[config_type] = {'total': 0, 'successful': 0}
            type_stats[config_type]['total'] += 1
            if result.success:
                type_stats[config_type]['successful'] += 1
        
        delays = [r.delay for r in results if r.success]
        avg_delay = sum(delays) / len(delays) if delays else 0
        min_delay = min(delays) if delays else 0
        max_delay = max(delays) if delays else 0
        
        return {
            'total_configs': total_configs,
            'successful_configs': successful_configs,
            'success_rate': (successful_configs / total_configs * 100) if total_configs > 0 else 0,
            'type_stats': type_stats,
            'avg_delay': avg_delay,
            'min_delay': min_delay,
            'max_delay': max_delay
        }

    def generate_delay_chart(self, results: List[TestResult], filename: str) -> bool:
        try:
            successful_results = [r for r in results if r.success]
            if not successful_results:
                return False
            
            delays = [r.delay for r in successful_results]
            names = [r.config.name for r in successful_results]
            
            plt.figure(figsize=(12, 6))
            plt.bar(names, delays)
            plt.xticks(rotation=45, ha='right')
            plt.xlabel('Config Name')
            plt.ylabel('Delay (ms)')
            plt.title('Config Delays')
            plt.tight_layout()
            
            plt.savefig(filename)
            plt.close()
            return True
        except Exception as e:
            print(f"Error generating chart: {e}")
            return False

class ReportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_generator = ReportGenerator()
        self.test_results = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # انتخاب نوع گزارش
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("فرمت گزارش:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "PDF"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        # خلاصه آماری
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)
        
        # دکمه‌های کنترل
        buttons_layout = QHBoxLayout()
        self.generate_button = QPushButton("ایجاد گزارش")
        self.generate_button.clicked.connect(self._generate_report)
        self.export_chart_button = QPushButton("نمودار تاخیر")
        self.export_chart_button.clicked.connect(self._export_chart)
        
        buttons_layout.addWidget(self.generate_button)
        buttons_layout.addWidget(self.export_chart_button)
        layout.addLayout(buttons_layout)

    def set_results(self, results: List[TestResult]):
        self.test_results = results
        self._update_summary()

    def _update_summary(self):
        if not self.test_results:
            self.summary_text.setText("هیچ نتیجه‌ای موجود نیست")
            return
        
        summary = self.report_generator.generate_summary(self.test_results)
        
        text = "خلاصه نتایج:\n\n"
        text += f"تعداد کل کانفیگ‌ها: {summary['total_configs']}\n"
        text += f"کانفیگ‌های موفق: {summary['successful_configs']}\n"
        text += f"نرخ موفقیت: {summary['success_rate']:.1f}%\n\n"
        
        text += "آمار بر اساس نوع:\n"
        for config_type, stats in summary['type_stats'].items():
            success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            text += f"{config_type}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)\n"
        
        text += f"\nمیانگین تاخیر: {summary['avg_delay']:.1f} ms\n"
        text += f"کمترین تاخیر: {summary['min_delay']:.1f} ms\n"
        text += f"بیشترین تاخیر: {summary['max_delay']:.1f} ms"
        
        self.summary_text.setText(text)

    def _generate_report(self):
        if not self.test_results:
            return
        
        report_format = self.format_combo.currentText()
        filters = "CSV Files (*.csv)" if report_format == "CSV" else "PDF Files (*.pdf)"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره گزارش",
            "",
            filters
        )
        
        if filename:
            if report_format == "CSV":
                success = self.report_generator.generate_csv(self.test_results, filename)
            else:  # PDF
                success = self.report_generator.generate_pdf(self.test_results, filename)
            
            if success:
                self.parent().parent().statusBar().showMessage(
                    f"گزارش با موفقیت در {filename} ذخیره شد",
                    5000
                )

    def _export_chart(self):
        if not self.test_results:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره نمودار",
            "",
            "PNG Files (*.png)"
        )
        
        if filename:
            if self.report_generator.generate_delay_chart(self.test_results, filename):
                self.parent().parent().statusBar().showMessage(
                    f"نمودار با موفقیت در {filename} ذخیره شد",
                    5000
                )
