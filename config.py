"""
配置文件
"""
import os

# 数据库配置
DB_NAME = "stock_data.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)

# 应用配置
APP_NAME = "股票数据分析系统"
APP_VERSION = "1.0.0"

# 表格配置
DEFAULT_PAGE_SIZE = 500  # 每页显示行数
MAX_DISPLAY_ROWS = 10000  # 最大显示行数

# Excel列名映射（根据您的数据格式）
COLUMN_MAPPING = {
    '交易日期': 'trade_date',
    '股票代码': 'stock_code',
    '股票名称': 'stock_name',
    '当前价格': 'current_price',
    '涨幅': 'price_change',  # 新增
    '描述': 'description',   # 新增
    '板块': 'sector',
    '主力净额': 'main_net_amount',
    '成交额': 'auction_today_volume',
    '实流市值': 'real_market_value',  # 新增
    '净流占比': 'flow_ratio',
    '净成占比': 'net_ratio',
    '实换手率': 'real_turnover_rate',  # 新增
    '换手率': 'turnover_rate',
    '量比': 'volume_ratio',
    '人气值': 'popularity_value',
    # 旧字段（如果Excel中有这些列，也会导入）
    '竞价净额': 'auction_net_amount',
    '竞价增额': 'auction_increase',
    '增额': 'auction_main_net',
    '今日成交额': 'auction_today_volume',
    '昨日成交额': 'auction_yesterday_volume',
    '主力净额对比': 'main_net_ratio',
    '夹流比': 'flow_ratio',
    '买卖手': 'buy_sell_ratio',
    '入气值增幅': 'popularity_change',
}

# 显示列定义（根据您的实际数据调整）
DISPLAY_COLUMNS = [
    {'key': 'trade_date', 'name': '交易日期', 'width': 100},
    {'key': 'stock_code', 'name': '股票代码', 'width': 100},
    {'key': 'stock_name', 'name': '股票名称', 'width': 100},
    {'key': 'current_price', 'name': '当前价格', 'width': 80},
    {'key': 'price_change', 'name': '涨幅', 'width': 70},
    {'key': 'sector', 'name': '板块', 'width': 150},
    {'key': 'main_net_amount', 'name': '主力净额', 'width': 100},
    {'key': 'main_net_prev_ratio', 'name': '主力净额前日对比', 'width': 120},
    {'key': 'auction_today_volume', 'name': '成交额', 'width': 100},
    {'key': 'volume_prev_ratio', 'name': '成交额前日对比', 'width': 120},
    {'key': 'real_market_value', 'name': '实流市值', 'width': 100},
    {'key': 'flow_ratio', 'name': '净流占比', 'width': 80},
    {'key': 'net_ratio', 'name': '净成占比', 'width': 80},
    {'key': 'real_turnover_rate', 'name': '实换手率', 'width': 80},
    {'key': 'turnover_rate', 'name': '换手率', 'width': 80},
    {'key': 'volume_ratio', 'name': '量比', 'width': 80},
    {'key': 'popularity_value', 'name': '人气值', 'width': 80},
]

