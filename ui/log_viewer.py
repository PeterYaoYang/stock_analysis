"""
日志查看器窗口
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton,
    QHBoxLayout, QLabel, QComboBox
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QTextCursor


class LogViewer(QDialog):
    """日志查看器"""
    
    def __init__(self, log_file="stock_analysis.log", parent=None):
        super().__init__(parent)
        self.log_file = log_file
        self.auto_refresh = False
        self.init_ui()
        self.load_log()
        
        # 自动刷新定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_log)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("系统日志查看器")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        # 日志级别筛选
        toolbar.addWidget(QLabel("日志级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "INFO", "WARNING", "ERROR", "DEBUG"])
        self.level_combo.currentTextChanged.connect(self.filter_log)
        toolbar.addWidget(self.level_combo)
        
        toolbar.addStretch()
        
        # 刷新按钮
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self.load_log)
        toolbar.addWidget(btn_refresh)
        
        # 自动刷新按钮
        self.btn_auto_refresh = QPushButton("⏸ 自动刷新")
        self.btn_auto_refresh.setCheckable(True)
        self.btn_auto_refresh.toggled.connect(self.toggle_auto_refresh)
        toolbar.addWidget(self.btn_auto_refresh)
        
        # 清空日志按钮
        btn_clear = QPushButton("🗑 清空日志")
        btn_clear.clicked.connect(self.clear_log)
        toolbar.addWidget(btn_clear)
        
        # 导出按钮
        btn_export = QPushButton("💾 导出")
        btn_export.clicked.connect(self.export_log)
        toolbar.addWidget(btn_export)
        
        layout.addLayout(toolbar)
        
        # 日志文本显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        
        # 设置样式
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #444;
            }
        """)
        
        layout.addWidget(self.log_text)
        
        # 底部状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.line_count_label = QLabel("共 0 行")
        status_layout.addWidget(self.line_count_label)
        
        layout.addLayout(status_layout)
        
        # 关闭按钮
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
    
    def load_log(self):
        """加载日志文件"""
        if not os.path.exists(self.log_file):
            self.log_text.setPlainText("日志文件不存在")
            self.status_label.setText("日志文件不存在")
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示最后1000行
            lines = content.split('\n')
            if len(lines) > 1000:
                lines = lines[-1000:]
                content = '\n'.join(lines)
            
            self.full_log = content
            self.filter_log()
            
            # 更新状态
            file_size = os.path.getsize(self.log_file) / 1024  # KB
            self.status_label.setText(f"日志文件: {file_size:.2f} KB")
            
            # 滚动到底部
            self.log_text.moveCursor(QTextCursor.End)
            
        except Exception as e:
            self.log_text.setPlainText(f"加载日志失败: {str(e)}")
            self.status_label.setText(f"加载失败: {str(e)}")
    
    def filter_log(self):
        """筛选日志"""
        level = self.level_combo.currentText()
        
        if level == "全部":
            filtered_content = self.full_log
        else:
            lines = self.full_log.split('\n')
            filtered_lines = [line for line in lines if level in line]
            filtered_content = '\n'.join(filtered_lines)
        
        # 高亮显示不同级别
        html_content = self.format_log_html(filtered_content)
        self.log_text.setHtml(html_content)
        
        # 更新行数
        line_count = len(filtered_content.split('\n'))
        self.line_count_label.setText(f"共 {line_count} 行")
    
    def format_log_html(self, content):
        """格式化日志为HTML（带颜色）"""
        lines = content.split('\n')
        html_lines = []
        
        for line in lines:
            if 'ERROR' in line:
                color = '#f48771'  # 红色
            elif 'WARNING' in line:
                color = '#dcdcaa'  # 黄色
            elif 'INFO' in line:
                color = '#4ec9b0'  # 青色
            elif 'DEBUG' in line:
                color = '#858585'  # 灰色
            else:
                color = '#d4d4d4'  # 白色
            
            html_lines.append(f'<span style="color:{color};">{line}</span>')
        
        return '<pre style="font-family: Consolas; font-size: 9pt;">' + '<br>'.join(html_lines) + '</pre>'
    
    def toggle_auto_refresh(self, checked):
        """切换自动刷新"""
        self.auto_refresh = checked
        if checked:
            self.btn_auto_refresh.setText("⏸ 停止刷新")
            self.timer.start(2000)  # 每2秒刷新一次
            self.status_label.setText("自动刷新已启用")
        else:
            self.btn_auto_refresh.setText("▶ 自动刷新")
            self.timer.stop()
            self.status_label.setText("自动刷新已停止")
    
    def clear_log(self):
        """清空日志文件"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, '确认',
            '确定要清空日志文件吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write('')
                self.load_log()
                self.status_label.setText("日志已清空")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空日志失败: {str(e)}")
    
    def export_log(self):
        """导出日志"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "stock_analysis_log.txt", "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.full_log)
                QMessageBox.information(self, "成功", f"日志已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def closeEvent(self, event):
        """关闭事件"""
        self.timer.stop()
        event.accept()

