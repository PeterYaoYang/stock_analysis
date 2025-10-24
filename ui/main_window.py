"""
主窗口
"""
import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QAction, QFileDialog, QMessageBox, QLabel,
    QStatusBar, QPushButton, QSplitter, QProgressDialog
)
from PyQt5.QtCore import Qt, QTimer, QCoreApplication
from PyQt5.QtGui import QIcon
import logging

from ui.data_table_view import DataTableView
from ui.filter_panel import FilterPanel
from ui.data_import_dialog import DataImportDialog
from ui.log_viewer import LogViewer
from database import DatabaseManager
from data_processor import ExcelParser
from utils.thread_worker import WorkerThread
import config


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager(config.DB_PATH)
        self.excel_parser = ExcelParser()
        self.current_data = None
        self.worker_thread = None  # 用于异步加载数据的线程
        self.progress_dialog = None  # 加载进度对话框
        
        self.init_ui()
        self.load_initial_data()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.setGeometry(100, 100, 1600, 900)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建工具栏区域
        toolbar_layout = QHBoxLayout()
        
        # 导入数据按钮
        btn_import = QPushButton("📁 批量导入数据")
        btn_import.clicked.connect(self.open_import_dialog)
        btn_import.setStyleSheet("""
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
        """)
        
        # 刷新按钮
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self.refresh_data)
        
        # 导出按钮
        btn_export = QPushButton("📥 导出到Excel")
        btn_export.clicked.connect(self.export_data)
        
        # 统计按钮
        btn_statistics = QPushButton("📊 统计信息")
        btn_statistics.clicked.connect(self.show_statistics)
        
        # 日志按钮
        btn_log = QPushButton("📋 查看日志")
        btn_log.clicked.connect(self.show_log_viewer)
        btn_log.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        toolbar_layout.addWidget(btn_import)
        toolbar_layout.addWidget(btn_refresh)
        toolbar_layout.addWidget(btn_export)
        toolbar_layout.addWidget(btn_statistics)
        toolbar_layout.addWidget(btn_log)
        toolbar_layout.addStretch()
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建分割器（筛选面板 + 数据表格）
        splitter = QSplitter(Qt.Vertical)
        
        # 筛选面板
        self.filter_panel = FilterPanel(self.db_manager)
        self.filter_panel.filter_applied.connect(self.apply_filter)
        splitter.addWidget(self.filter_panel)
        
        # 数据表格
        self.table_view = DataTableView()
        splitter.addWidget(self.table_view)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)  # 筛选面板
        splitter.setStretchFactor(1, 4)  # 数据表格
        
        main_layout.addWidget(splitter)
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        import_action = QAction('导入数据', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.open_import_dialog)
        file_menu.addAction(import_action)
        
        export_action = QAction('导出数据', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 数据菜单
        data_menu = menubar.addMenu('数据')
        
        refresh_action = QAction('刷新', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_data)
        data_menu.addAction(refresh_action)
        
        clear_filter_action = QAction('清除筛选', self)
        clear_filter_action.setShortcut('Ctrl+R')
        clear_filter_action.triggered.connect(self.clear_filter)
        data_menu.addAction(clear_filter_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        log_action = QAction('查看日志', self)
        log_action.setShortcut('Ctrl+L')
        log_action.triggered.connect(self.show_log_viewer)
        tools_menu.addAction(log_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.statusBar.addWidget(self.status_label)
        
        # 记录数标签
        self.records_label = QLabel("共 0 条数据")
        self.statusBar.addPermanentWidget(self.records_label)
        
        # 数据库大小标签
        self.db_size_label = QLabel("数据库: 0 MB")
        self.statusBar.addPermanentWidget(self.db_size_label)
        
        self.update_status_bar()
    
    def update_status_bar(self):
        """更新状态栏"""
        # 更新数据库大小
        if os.path.exists(config.DB_PATH):
            size_mb = os.path.getsize(config.DB_PATH) / (1024 * 1024)
            self.db_size_label.setText(f"数据库: {size_mb:.2f} MB")
    
    def load_initial_data(self):
        """加载初始数据"""
        # 获取最近的交易日期
        dates = self.db_manager.get_all_dates()
        if dates:
            latest_date = dates[0]
            self.load_data_by_date(latest_date)
            self.status_label.setText(f"已加载 {latest_date} 的数据")
        else:
            self.status_label.setText("数据库为空，请导入数据")
    
    def load_data_by_date(self, trade_date: str):
        """按日期加载数据（包含前日对比） - 异步方式"""
        # 如果有正在运行的线程，不启动新查询
        if self.worker_thread and self.worker_thread.isRunning():
            logging.warning("已有查询正在进行中，请稍候")
            return
        
        # 设置加载状态和进度提示
        self.set_loading_state(True, f"正在加载 {trade_date} 的数据...")
        self.status_label.setText(f"正在加载 {trade_date} 的数据...")
        
        # 创建工作线程执行查询
        self.worker_thread = WorkerThread(
            self.db_manager.query_by_date_with_comparison,
            trade_date,
            limit=config.MAX_DISPLAY_ROWS
        )
        
        # 连接信号
        self.worker_thread.task_completed.connect(
            lambda df: self.on_data_loaded(df, trade_date)
        )
        self.worker_thread.task_failed.connect(self.on_data_load_failed)
        
        # 启动线程
        self.worker_thread.start()
    
    def open_import_dialog(self):
        """打开导入对话框"""
        dialog = DataImportDialog(self.db_manager, self.excel_parser, self)
        if dialog.exec_():
            # 导入成功，刷新数据
            self.refresh_data()
            self.update_status_bar()
    
    def apply_filter(self, filter_params: dict):
        """应用筛选（包含前日对比） - 异步方式"""
        trade_date = filter_params.get('trade_date')
        stock_code = filter_params.get('stock_code')
        sector = filter_params.get('sector')
        
        if not trade_date:
            QMessageBox.warning(self, "提示", "请选择交易日期")
            return
        
        # 如果有正在运行的线程，不启动新查询
        if self.worker_thread and self.worker_thread.isRunning():
            logging.warning("已有查询正在进行中，请稍候")
            return
        
        # 设置加载状态和进度提示
        filter_desc = f"{trade_date}"
        if stock_code:
            filter_desc += f" (代码: {stock_code})"
        if sector:
            filter_desc += f" (板块: {sector})"
        
        self.set_loading_state(True, f"正在筛选数据...\n{filter_desc}")
        self.status_label.setText("正在筛选数据...")
        
        # 创建工作线程执行查询
        self.worker_thread = WorkerThread(
            self.db_manager.query_by_date_with_comparison,
            trade_date,
            stock_code=stock_code,
            sector=sector,
            limit=config.MAX_DISPLAY_ROWS
        )
        
        # 连接信号
        self.worker_thread.task_completed.connect(
            lambda df: self.on_data_loaded(df, trade_date, stock_code, sector)
        )
        self.worker_thread.task_failed.connect(self.on_data_load_failed)
        
        # 启动线程
        self.worker_thread.start()
    
    def set_loading_state(self, is_loading: bool, message: str = "正在加载数据，请稍候..."):
        """设置加载状态"""
        # 禁用/启用筛选面板
        self.filter_panel.set_enabled(not is_loading)
        
        # 禁用/启用表格排序（加载时禁止）
        if is_loading:
            self.table_view.table.setSortingEnabled(False)
            
            # 显示进度对话框
            if self.progress_dialog is None:
                self.progress_dialog = QProgressDialog(
                    message,
                    None,  # 不显示取消按钮
                    0, 0,  # 0到0表示不确定的进度
                    self
                )
                self.progress_dialog.setWindowTitle("加载中")
                self.progress_dialog.setWindowModality(Qt.WindowModal)
                self.progress_dialog.setMinimumDuration(0)  # 立即显示
                self.progress_dialog.setAutoClose(True)
                self.progress_dialog.setAutoReset(True)
                
                # 设置对话框样式
                self.progress_dialog.setStyleSheet("""
                    QProgressDialog {
                        min-width: 350px;
                        min-height: 120px;
                    }
                    QProgressBar {
                        border: 2px solid #667eea;
                        border-radius: 5px;
                        text-align: center;
                        height: 25px;
                    }
                    QProgressBar::chunk {
                        background-color: #667eea;
                    }
                    QLabel {
                        font-size: 13px;
                        padding: 10px;
                    }
                """)
            else:
                # 更新进度对话框的文本
                self.progress_dialog.setLabelText(message)
            
            self.progress_dialog.show()
        else:
            # 隐藏进度对话框
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
    
    def on_data_loaded(self, df, trade_date, stock_code=None, sector=None):
        """数据加载完成的回调"""
        try:
            # 更新进度提示
            if self.progress_dialog:
                self.progress_dialog.setLabelText(f"正在填充表格...\n共 {len(df)} 条数据")
                # 处理事件队列，让进度条保持响应
                QCoreApplication.processEvents()
            
            self.current_data = df
            self.table_view.set_data(df)
            self.records_label.setText(f"共 {len(df)} 条数据")
            
            # 构建状态消息
            if stock_code or sector:
                filters = []
                if stock_code:
                    filters.append(f"代码:{stock_code}")
                if sector:
                    filters.append(f"板块:{sector}")
                filter_str = ", ".join(filters)
                self.status_label.setText(f"筛选完成: {trade_date} ({filter_str})")
            else:
                self.status_label.setText(f"加载完成: {trade_date}")
            
            logging.info(f"加载了 {len(df)} 条数据，日期: {trade_date}")
        except Exception as e:
            logging.error(f"显示数据失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"显示数据失败: {str(e)}")
        finally:
            # 恢复UI状态
            self.set_loading_state(False)
    
    def on_data_load_failed(self, error_msg: str):
        """数据加载失败的回调"""
        QMessageBox.critical(self, "错误", f"加载数据失败: {error_msg}")
        logging.error(f"加载数据失败: {error_msg}")
        self.status_label.setText("加载失败")
        
        # 恢复UI状态
        self.set_loading_state(False)
    
    def clear_filter(self):
        """清除筛选"""
        self.filter_panel.clear_filters()
        self.load_initial_data()
    
    def refresh_data(self):
        """刷新数据"""
        self.load_initial_data()
        self.filter_panel.update_date_list()
        self.update_status_bar()
        self.status_label.setText("数据已刷新")
    
    def export_data(self):
        """导出数据到Excel"""
        if self.current_data is None or len(self.current_data) == 0:
            QMessageBox.warning(self, "提示", "没有可导出的数据")
            return
        
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出数据", "", "Excel文件 (*.xlsx)"
            )
            
            if file_path:
                # 导出到Excel
                self.current_data.to_excel(file_path, index=False, engine='openpyxl')
                QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
                logging.info(f"数据已导出: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
            logging.error(f"导出失败: {str(e)}")
    
    def show_statistics(self):
        """显示统计信息"""
        dates = self.db_manager.get_all_dates()
        if not dates:
            QMessageBox.information(self, "统计信息", "数据库中没有数据")
            return
        
        latest_date = dates[0]
        stats = self.db_manager.get_statistics(latest_date)
        
        msg = f"""
        <h3>统计信息 - {latest_date}</h3>
        <p><b>总股票数:</b> {stats['total_count']}</p>
        <p><b>主力净流入股票数:</b> {stats['positive_main_count']}</p>
        <p><b>成交额增长股票数:</b> {stats['positive_volume_count']}</p>
        <p><b>平均换手率:</b> {stats['avg_turnover']}%</p>
        <hr>
        <p><b>数据库中共有 {len(dates)} 个交易日的数据</b></p>
        """
        
        QMessageBox.information(self, "统计信息", msg)
    
    def show_log_viewer(self):
        """显示日志查看器"""
        log_viewer = LogViewer(parent=self)
        log_viewer.exec_()
    
    def show_about(self):
        """显示关于对话框"""
        msg = f"""
        <h2>{config.APP_NAME}</h2>
        <p>版本: {config.APP_VERSION}</p>
        <p>基于 Python + PyQt5 + SQLite 构建</p>
        <p>支持海量股票数据的快速查询与分析</p>
        <hr>
        <p>技术栈:</p>
        <ul>
            <li>PyQt5 - 图形界面</li>
            <li>pandas - 数据处理</li>
            <li>SQLite - 数据存储</li>
            <li>openpyxl - Excel处理</li>
        </ul>
        <hr>
        <p><b>快捷键:</b></p>
        <ul>
            <li>Ctrl+I - 导入数据</li>
            <li>Ctrl+E - 导出数据</li>
            <li>Ctrl+R - 清除筛选</li>
            <li>Ctrl+L - 查看日志</li>
            <li>F5 - 刷新</li>
        </ul>
        """
        QMessageBox.about(self, "关于", msg)
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出程序吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 停止运行中的线程
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.terminate()
                self.worker_thread.wait()
            
            # 关闭进度对话框
            if self.progress_dialog:
                self.progress_dialog.close()
            
            # 关闭数据库连接
            self.db_manager.close()
            event.accept()
        else:
            event.ignore()

