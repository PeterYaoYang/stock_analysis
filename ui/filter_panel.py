"""
筛选面板
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QGroupBox
)
from PyQt5.QtCore import pyqtSignal
import logging


class FilterPanel(QWidget):
    """筛选面板"""
    
    # 信号定义
    filter_applied = pyqtSignal(dict)  # 筛选应用信号
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
        self.update_date_list()
    
    def init_ui(self):
        """初始化UI"""
        # 创建分组框
        group_box = QGroupBox("数据筛选")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(group_box)
        
        # 分组框内的布局
        layout = QHBoxLayout()
        group_box.setLayout(layout)
        
        # 日期选择
        date_layout = QHBoxLayout()
        date_label = QLabel("交易日期:")
        self.date_combo = QComboBox()
        self.date_combo.setMinimumWidth(150)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_combo)
        
        # 股票搜索
        search_layout = QHBoxLayout()
        search_label = QLabel("股票搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入股票代码或名称...")
        self.search_input.setMinimumWidth(200)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        # 板块筛选
        sector_layout = QHBoxLayout()
        sector_label = QLabel("板块:")
        self.sector_combo = QComboBox()
        self.sector_combo.addItem("全部", None)
        self.sector_combo.setMinimumWidth(150)
        sector_layout.addWidget(sector_label)
        sector_layout.addWidget(self.sector_combo)
        
        # 应用筛选按钮
        self.btn_apply = QPushButton("🔍 应用筛选")
        self.btn_apply.clicked.connect(self.apply_filter)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        # 清除筛选按钮
        self.btn_clear = QPushButton("✖ 清除")
        self.btn_clear.clicked.connect(self.clear_filters)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        # 添加到主布局
        layout.addLayout(date_layout)
        layout.addLayout(search_layout)
        layout.addLayout(sector_layout)
        layout.addWidget(self.btn_apply)
        layout.addWidget(self.btn_clear)
        layout.addStretch()
        
        # 回车键触发筛选
        self.search_input.returnPressed.connect(self.apply_filter)
    
    def update_date_list(self):
        """更新日期列表"""
        try:
            dates = self.db_manager.get_all_dates()
            self.date_combo.clear()
            
            if dates:
                for date in dates:
                    self.date_combo.addItem(date, date)
                
                # 更新板块列表
                self.update_sector_list()
            else:
                logging.warning("数据库中没有日期数据")
                
        except Exception as e:
            logging.error(f"更新日期列表失败: {str(e)}")
    
    def update_sector_list(self):
        """更新板块列表"""
        try:
            sectors = self.db_manager.get_all_sectors()
            self.sector_combo.clear()
            self.sector_combo.addItem("全部", None)
            
            for sector in sectors:
                if sector:
                    self.sector_combo.addItem(sector, sector)
                    
        except Exception as e:
            logging.error(f"更新板块列表失败: {str(e)}")
    
    def apply_filter(self):
        """应用筛选"""
        # 获取筛选参数
        filter_params = {
            'trade_date': self.date_combo.currentData(),
            'stock_code': self.search_input.text().strip() if self.search_input.text().strip() else None,
            'sector': self.sector_combo.currentData()
        }
        
        # 发送信号
        self.filter_applied.emit(filter_params)
        logging.info(f"应用筛选: {filter_params}")
    
    def clear_filters(self):
        """清除筛选"""
        self.search_input.clear()
        self.sector_combo.setCurrentIndex(0)
        
        # 应用清除后的筛选
        self.apply_filter()
    
    def get_current_date(self) -> str:
        """获取当前选中的日期"""
        return self.date_combo.currentData()
    
    def set_enabled(self, enabled: bool):
        """设置筛选面板的启用/禁用状态"""
        self.date_combo.setEnabled(enabled)
        self.search_input.setEnabled(enabled)
        self.sector_combo.setEnabled(enabled)
        self.btn_apply.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)

