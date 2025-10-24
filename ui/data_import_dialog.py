"""
数据导入对话框
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt
import logging

from utils.thread_worker import BatchImportWorker
import config


class DataImportDialog(QDialog):
    """数据导入对话框"""
    
    def __init__(self, db_manager, excel_parser, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.excel_parser = excel_parser
        self.file_paths = []
        self.worker = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("批量导入数据")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # 说明文字
        info_label = QLabel(
            "选择包含Excel文件的文件夹，系统会自动识别日期并导入数据。\n"
            "支持格式: .xlsx, .xls\n"
            "文件名示例: 2025-09-01.xlsx"
        )
        info_label.setStyleSheet("color: #666; padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # 文件选择区域
        file_group = QGroupBox("选择文件")
        file_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        
        # 选择文件按钮
        self.btn_select_files = QPushButton("📄 选择单个文件")
        self.btn_select_files.clicked.connect(self.select_files)
        
        # 选择文件夹按钮
        self.btn_select_folder = QPushButton("📁 选择文件夹")
        self.btn_select_folder.clicked.connect(self.select_folder)
        
        btn_layout.addWidget(self.btn_select_files)
        btn_layout.addWidget(self.btn_select_folder)
        btn_layout.addStretch()
        
        file_layout.addLayout(btn_layout)
        
        # 已选择文件列表
        self.file_list_label = QLabel("未选择文件")
        self.file_list_label.setStyleSheet("color: #999; font-style: italic;")
        file_layout.addWidget(self.file_list_label)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 进度条
        progress_group = QGroupBox("导入进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("等待开始...")
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 日志输出
        log_group = QGroupBox("导入日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("开始导入")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_import)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.close_dialog)
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def select_files(self):
        """选择单个或多个文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择Excel文件", "", 
            "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_paths:
            self.file_paths = file_paths
            self.update_file_list()
            self.btn_start.setEnabled(True)
    
    def select_folder(self):
        """选择文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择包含Excel文件的文件夹")
        
        if folder_path:
            # 递归查找所有Excel文件
            self.file_paths = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')) and not file.startswith('~'):
                        self.file_paths.append(os.path.join(root, file))
            
            if self.file_paths:
                self.update_file_list()
                self.btn_start.setEnabled(True)
            else:
                QMessageBox.warning(self, "提示", "该文件夹中没有找到Excel文件")
    
    def update_file_list(self):
        """更新文件列表显示"""
        count = len(self.file_paths)
        if count > 0:
            self.file_list_label.setText(f"已选择 {count} 个文件")
            self.file_list_label.setStyleSheet("color: #28a745; font-weight: bold;")
            
            # 在日志中显示文件列表
            self.log_text.clear()
            self.log_text.append(f"准备导入 {count} 个文件:\n")
            for idx, path in enumerate(self.file_paths[:10], 1):
                self.log_text.append(f"{idx}. {os.path.basename(path)}")
            if count > 10:
                self.log_text.append(f"... 还有 {count - 10} 个文件")
    
    def start_import(self):
        """开始导入"""
        if not self.file_paths:
            QMessageBox.warning(self, "提示", "请先选择文件")
            return
        
        # 禁用按钮
        self.btn_start.setEnabled(False)
        self.btn_select_files.setEnabled(False)
        self.btn_select_folder.setEnabled(False)
        
        # 清空日志
        self.log_text.clear()
        self.log_text.append("开始导入...\n")
        
        # 创建工作线程
        self.worker = BatchImportWorker(
            self.file_paths,
            self.db_manager,
            self.excel_parser,
            config.COLUMN_MAPPING
        )
        
        # 连接信号
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.file_imported.connect(self.on_file_imported)
        self.worker.all_completed.connect(self.on_all_completed)
        
        # 启动线程
        self.worker.start()
    
    def on_progress_updated(self, current: int, total: int, filename: str):
        """进度更新"""
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"正在导入 ({current}/{total}): {filename}")
    
    def on_file_imported(self, filename: str, records: int, success: bool, message: str):
        """文件导入完成"""
        if success:
            self.log_text.append(f"✓ {filename}: {message}")
        else:
            self.log_text.append(f"✗ {filename}: {message}")
        
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def on_all_completed(self, success_count: int, fail_count: int, total_records: int):
        """全部导入完成"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("导入完成！")
        
        # 显示总结
        self.log_text.append("\n" + "="*50)
        self.log_text.append(f"导入完成！")
        self.log_text.append(f"成功: {success_count} 个文件")
        self.log_text.append(f"失败: {fail_count} 个文件")
        self.log_text.append(f"总共导入: {total_records} 条记录")
        self.log_text.append("="*50)
        
        # 启用关闭按钮
        self.btn_cancel.setText("完成")
        
        # 显示消息框
        QMessageBox.information(
            self, "导入完成",
            f"成功导入 {success_count} 个文件，共 {total_records} 条记录"
        )
    
    def close_dialog(self):
        """关闭对话框"""
        # 如果正在导入，询问是否取消
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, '确认',
                '正在导入数据，确定要取消吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                self.reject()
        else:
            self.accept()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.worker and self.worker.isRunning():
            event.ignore()
            self.close_dialog()
        else:
            event.accept()

