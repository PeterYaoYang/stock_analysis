"""
数据表格视图
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QColor
import pandas as pd
import config


class NumericTableWidgetItem(QTableWidgetItem):
    """支持数值排序的表格项"""
    
    def __lt__(self, other):
        """重写小于比较，用于排序"""
        # 尝试获取UserRole数据进行数值比较
        self_data = self.data(Qt.UserRole)
        other_data = other.data(Qt.UserRole)
        
        # 如果两者都有UserRole数据，按数值比较
        if self_data is not None and other_data is not None:
            try:
                return float(self_data) < float(other_data)
            except (ValueError, TypeError):
                pass
        
        # 否则按文本比较
        return super().__lt__(other)


class DataTableView(QWidget):
    """数据表格视图"""
    
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        # 设置表格样式
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #ddd;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #667eea;
                color: white;
            }
            QHeaderView::section {
                background-color: #667eea;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # 设置列
        self.setup_columns()
        
        layout.addWidget(self.table)
    
    def setup_columns(self):
        """设置表格列"""
        self.table.setColumnCount(len(config.DISPLAY_COLUMNS))
        
        headers = [col['name'] for col in config.DISPLAY_COLUMNS]
        self.table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        for idx, col in enumerate(config.DISPLAY_COLUMNS):
            self.table.setColumnWidth(idx, col['width'])
        
        # 设置最后一列自适应
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def set_data(self, df: pd.DataFrame):
        """设置数据"""
        self.current_data = df
        self.populate_table(df)
    
    def populate_table(self, df: pd.DataFrame):
        """填充表格数据"""
        if df is None or len(df) == 0:
            self.table.setRowCount(0)
            return
        
        # 优化性能：禁用UI更新和信号
        self.table.setSortingEnabled(False)
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        
        # 设置行数
        row_count = min(len(df), config.MAX_DISPLAY_ROWS)
        self.table.setRowCount(row_count)
        
        # 填充数据
        for row_idx in range(row_count):
            for col_idx, col_config in enumerate(config.DISPLAY_COLUMNS):
                col_key = col_config['key']
                
                # 获取值
                if col_key in df.columns:
                    value = df.iloc[row_idx][col_key]
                    
                    # 格式化显示
                    display_text = self.format_value(value, col_key)
                    
                    # 为对比字段使用数值排序项，其他使用普通项
                    if col_key in ['main_net_prev_ratio', 'volume_prev_ratio']:
                        item = NumericTableWidgetItem(display_text)
                        # 设置排序数据（使用原始数值）
                        try:
                            float_value = float(value) if not pd.isna(value) else 0.0
                            item.setData(Qt.UserRole, float_value)
                        except (ValueError, TypeError):
                            item.setData(Qt.UserRole, 0.0)
                    else:
                        item = QTableWidgetItem(display_text)
                    
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # 设置颜色（主力净额、对比等）
                    self.apply_color(item, value, col_key)
                    
                    self.table.setItem(row_idx, col_idx, item)
            
            # 每处理50行，处理一次事件队列，让进度条保持响应
            if (row_idx + 1) % 50 == 0:
                QCoreApplication.processEvents()
        
        # 调整行高
        self.table.verticalHeader().setDefaultSectionSize(35)
        
        # 恢复UI更新和信号，重新启用排序
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(True)
    
    def format_value(self, value, col_key: str) -> str:
        """格式化值"""
        if pd.isna(value) or value is None:
            return ""
        
        # 需要显示"万/亿"单位的字段（数据库中存储的单位是"万"）
        money_cols = [
            'auction_today_volume',      # 成交额
            'auction_yesterday_volume',   # 昨日成交额
            'real_market_value',          # 实流市值
            'main_net_amount',            # 主力净额
            'auction_net_amount',         # 竞价净额
            'auction_main_net',           # 增额
        ]
        
        # 百分比字段
        percent_cols = [
            'price_change',          # 涨幅
            'flow_ratio',            # 净流占比
            'net_ratio',             # 净成占比
            'turnover_rate',         # 换手率
            'real_turnover_rate',    # 实换手率
        ]
        
        # 对比比率字段（显示为倍数）
        ratio_cols = [
            'main_net_prev_ratio',   # 主力净额前日对比
            'volume_prev_ratio',     # 成交额前日对比
        ]
        
        # 格式化金额字段（带万/亿单位）
        if col_key in money_cols:
            try:
                num_value = float(value)
                return self._format_money(num_value)
            except (ValueError, TypeError):
                return str(value)
        
        # 格式化对比比率字段（显示为倍数或百分比）
        if col_key in ratio_cols:
            try:
                num_value = float(value)
                return self._format_ratio(num_value)
            except (ValueError, TypeError):
                return "-"
        
        # 格式化百分比字段
        if col_key in percent_cols:
            try:
                num_value = float(value)
                if abs(num_value) >= 100:
                    return f"{num_value:.2f}%"
                elif abs(num_value) >= 10:
                    return f"{num_value:.2f}%"
                else:
                    return f"{num_value:.2f}%"
            except (ValueError, TypeError):
                return str(value)
        
        # 其他数值字段
        numeric_cols = [
            'current_price', 'buy_sell_ratio', 'volume_ratio',
            'popularity_value', 'popularity_change', 'main_net_ratio'
        ]
        
        if col_key in numeric_cols:
            try:
                num_value = float(value)
                # 根据数值大小决定小数位
                if abs(num_value) >= 1000:
                    return f"{num_value:.1f}"
                elif abs(num_value) >= 100:
                    return f"{num_value:.2f}"
                elif abs(num_value) >= 1:
                    return f"{num_value:.2f}"
                else:
                    return f"{num_value:.3f}"
            except (ValueError, TypeError):
                return str(value)
        
        return str(value)
    
    def _format_money(self, value: float) -> str:
        """
        格式化金额显示（自动添加万/亿单位）
        数据库中存储的单位是"万"，需要转换为合适的显示单位
        
        Args:
            value: 数值（单位：万）
            
        Returns:
            格式化后的字符串，如 "3070万"、"7315.3亿"
        """
        if value == 0:
            return "0"
        
        abs_value = abs(value)
        
        # 如果大于等于10000万，显示为"亿"
        if abs_value >= 10000:
            yi_value = value / 10000
            # 根据数值大小决定小数位
            if abs(yi_value) >= 1000:
                return f"{yi_value:.1f}亿"
            elif abs(yi_value) >= 100:
                return f"{yi_value:.1f}亿"
            else:
                return f"{yi_value:.1f}亿"
        
        # 小于10000万，显示为"万"
        else:
            # 根据数值大小决定小数位
            if abs_value >= 1000:
                return f"{value:.1f}万"
            elif abs_value >= 100:
                return f"{value:.1f}万"
            elif abs_value >= 1:
                return f"{value:.1f}万"
            else:
                return f"{value:.2f}万"
    
    def _format_ratio(self, value: float) -> str:
        """
        格式化对比比率显示
        
        Args:
            value: 比率值（如：1.5表示1.5倍，0.8表示0.8倍）
            
        Returns:
            格式化后的字符串，统一为百分比格式，如 "50%"、"-20%"、"0%"
        """
        # 计算百分比变化
        percent_change = (value - 1) * 100
        
        # 统一显示为百分比，正数不带+号
        if percent_change == 0:
            return "0%"
        else:
            return f"{percent_change:.1f}%"
    
    def apply_color(self, item: QTableWidgetItem, value, col_key: str):
        """应用颜色"""
        # 主力净额相关列
        if col_key in ['main_net_amount', 'auction_net_amount']:
            try:
                num_value = float(value)
                if num_value > 0:
                    item.setForeground(QColor(220, 53, 69))  # 红色（流入）
                elif num_value < 0:
                    item.setForeground(QColor(40, 167, 69))  # 绿色（流出）
            except (ValueError, TypeError):
                pass
        
        # 主力净额对比
        elif col_key == 'main_net_ratio':
            try:
                ratio = float(value)
                if ratio > 1:
                    item.setForeground(QColor(220, 53, 69))  # 红色（增长）
                elif ratio < 1:
                    item.setForeground(QColor(40, 167, 69))  # 绿色（下降）
            except (ValueError, TypeError):
                pass
        
        # 前日对比列（主力净额前日对比、成交额前日对比）
        elif col_key in ['main_net_prev_ratio', 'volume_prev_ratio']:
            try:
                ratio = float(value)
                if ratio > 1:
                    item.setForeground(QColor(220, 53, 69))  # 红色（增长）
                    item.setFont(item.font())  # 保持原字体
                elif ratio < 1:
                    item.setForeground(QColor(40, 167, 69))  # 绿色（下降）
                # ratio == 1 保持默认颜色
            except (ValueError, TypeError):
                pass
        
        # 竞价增额（标记颜色）
        elif col_key == 'auction_increase':
            str_value = str(value).strip()
            if '5' in str_value or 'X5' in str_value:
                item.setBackground(QColor(220, 53, 69, 50))  # 浅红色背景
            elif '3' in str_value or 'X3' in str_value:
                item.setBackground(QColor(255, 193, 7, 50))  # 浅黄色背景
    
    def get_selected_row_data(self) -> dict:
        """获取选中行的数据"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return None
        
        row_idx = selected_rows[0].row()
        
        if self.current_data is None or row_idx >= len(self.current_data):
            return None
        
        return self.current_data.iloc[row_idx].to_dict()
    
    def clear(self):
        """清空表格"""
        self.table.setRowCount(0)
        self.current_data = None

