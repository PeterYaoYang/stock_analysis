"""
SQLite数据库管理模块
"""
import sqlite3
import logging
from typing import List, Dict, Tuple, Optional
import pandas as pd
from datetime import datetime


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库，创建表和索引"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.connection.cursor()
            
            # 创建股票日数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_daily (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    current_price REAL,
                    price_change REAL,
                    description TEXT,
                    sector TEXT,
                    main_net_amount REAL,
                    auction_today_volume REAL,
                    real_market_value REAL,
                    flow_ratio REAL,
                    net_ratio REAL,
                    real_turnover_rate REAL,
                    turnover_rate REAL,
                    volume_ratio REAL,
                    popularity_value REAL,
                    auction_net_amount REAL,
                    auction_increase TEXT,
                    auction_main_net REAL,
                    auction_yesterday_volume REAL,
                    main_net_ratio REAL,
                    buy_sell_ratio REAL,
                    popularity_change REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trade_date, stock_code)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON stock_daily(trade_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_code ON stock_daily(stock_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_code ON stock_daily(trade_date, stock_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sector ON stock_daily(sector)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_sector ON stock_daily(trade_date, sector)')
            
            # 创建数据导入历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS import_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_name TEXT,
                    trade_date TEXT,
                    records_count INTEGER,
                    status TEXT,
                    error_message TEXT
                )
            ''')
            
            self.connection.commit()
            logging.info("数据库初始化成功")
            
        except Exception as e:
            logging.error(f"数据库初始化失败: {str(e)}")
            raise
    
    def insert_batch(self, data: pd.DataFrame, trade_date: str) -> Tuple[int, int]:
        """
        批量插入数据
        
        Args:
            data: pandas DataFrame
            trade_date: 交易日期
            
        Returns:
            (成功插入数量, 跳过数量)
        """
        cursor = self.connection.cursor()
        inserted = 0
        skipped = 0
        
        for _, row in data.iterrows():
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_daily 
                    (trade_date, stock_code, stock_name, current_price, price_change,
                     description, sector, main_net_amount, auction_today_volume,
                     real_market_value, flow_ratio, net_ratio, real_turnover_rate,
                     turnover_rate, volume_ratio, popularity_value,
                     auction_net_amount, auction_increase, auction_main_net,
                     auction_yesterday_volume, main_net_ratio, buy_sell_ratio,
                     popularity_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_date,
                    row.get('stock_code'),
                    row.get('stock_name'),
                    row.get('current_price'),
                    row.get('price_change'),
                    row.get('description'),
                    row.get('sector'),
                    row.get('main_net_amount'),
                    row.get('auction_today_volume'),
                    row.get('real_market_value'),
                    row.get('flow_ratio'),
                    row.get('net_ratio'),
                    row.get('real_turnover_rate'),
                    row.get('turnover_rate'),
                    row.get('volume_ratio'),
                    row.get('popularity_value'),
                    row.get('auction_net_amount'),
                    row.get('auction_increase'),
                    row.get('auction_main_net'),
                    row.get('auction_yesterday_volume'),
                    row.get('main_net_ratio'),
                    row.get('buy_sell_ratio'),
                    row.get('popularity_change'),
                ))
                inserted += 1
            except Exception as e:
                logging.warning(f"插入数据失败: {str(e)}, 股票代码: {row.get('stock_code')}")
                skipped += 1
        
        self.connection.commit()
        return inserted, skipped
    
    def query_by_date(self, trade_date: str, 
                     stock_code: str = None,
                     sector: str = None,
                     limit: int = None) -> pd.DataFrame:
        """
        按日期查询数据
        
        Args:
            trade_date: 交易日期
            stock_code: 股票代码（可选）
            sector: 板块（可选）
            limit: 限制返回数量
            
        Returns:
            DataFrame
        """
        query = "SELECT * FROM stock_daily WHERE trade_date = ?"
        params = [trade_date]
        
        if stock_code:
            query += " AND stock_code = ?"
            params.append(stock_code)
        
        if sector:
            query += " AND sector LIKE ?"
            params.append(f"%{sector}%")
        
        # 默认按股票代码排序
        query += " ORDER BY stock_code ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return pd.read_sql_query(query, self.connection, params=params)
    
    def query_by_date_with_comparison(self, trade_date: str,
                                      stock_code: str = None,
                                      sector: str = None,
                                      limit: int = None) -> pd.DataFrame:
        """
        按日期查询数据，并计算与前一天的对比值
        
        Args:
            trade_date: 交易日期
            stock_code: 股票代码（可选）
            sector: 板块（可选）
            limit: 限制返回数量
            
        Returns:
            DataFrame (包含 main_net_prev_ratio 和 volume_prev_ratio 两列)
        """
        # 查询当天数据
        today_df = self.query_by_date(trade_date, stock_code, sector, limit)
        
        if today_df.empty:
            return today_df
        
        # 获取前一个交易日
        prev_date = self._get_previous_trade_date(trade_date)
        
        if prev_date is None:
            # 没有前一天数据，添加空列
            today_df['main_net_prev_ratio'] = None
            today_df['volume_prev_ratio'] = None
            logging.info(f"日期 {trade_date} 没有前一个交易日，对比列设为空")
            return today_df
        
        # 查询前一天数据
        prev_df = self.query_by_date(prev_date)
        
        if prev_df.empty:
            # 前一天没有数据
            today_df['main_net_prev_ratio'] = None
            today_df['volume_prev_ratio'] = None
            logging.warning(f"前一个交易日 {prev_date} 没有数据，对比列设为空")
            return today_df
        
        # 创建前一天数据的字典，以stock_code为键
        prev_dict = prev_df.set_index('stock_code')[['main_net_amount', 'auction_today_volume']].to_dict('index')
        
        # 计算对比值
        main_net_ratios = []
        volume_ratios = []
        
        for _, row in today_df.iterrows():
            code = row['stock_code']
            
            # 主力净额对比
            if code in prev_dict:
                today_main = row.get('main_net_amount')
                prev_main = prev_dict[code].get('main_net_amount')
                
                if pd.notna(today_main) and pd.notna(prev_main) and prev_main != 0:
                    main_ratio = today_main / prev_main
                else:
                    main_ratio = None
            else:
                main_ratio = None
            
            main_net_ratios.append(main_ratio)
            
            # 成交额对比
            if code in prev_dict:
                today_vol = row.get('auction_today_volume')
                prev_vol = prev_dict[code].get('auction_today_volume')
                
                if pd.notna(today_vol) and pd.notna(prev_vol) and prev_vol != 0:
                    vol_ratio = today_vol / prev_vol
                else:
                    vol_ratio = None
            else:
                vol_ratio = None
            
            volume_ratios.append(vol_ratio)
        
        # 添加对比列
        today_df['main_net_prev_ratio'] = main_net_ratios
        today_df['volume_prev_ratio'] = volume_ratios
        
        logging.info(f"已计算 {trade_date} 与 {prev_date} 的对比值")
        
        return today_df
    
    def _get_previous_trade_date(self, current_date: str) -> Optional[str]:
        """
        获取指定日期的前一个交易日
        
        Args:
            current_date: 当前日期
            
        Returns:
            前一个交易日，如果不存在则返回None
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT DISTINCT trade_date 
            FROM stock_daily 
            WHERE trade_date < ? 
            ORDER BY trade_date DESC 
            LIMIT 1
        """, (current_date,))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def query_by_date_range(self, start_date: str, end_date: str,
                           stock_code: str = None) -> pd.DataFrame:
        """
        按日期范围查询数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            stock_code: 股票代码（可选）
            
        Returns:
            DataFrame
        """
        query = "SELECT * FROM stock_daily WHERE trade_date BETWEEN ? AND ?"
        params = [start_date, end_date]
        
        if stock_code:
            query += " AND stock_code = ?"
            params.append(stock_code)
        
        query += " ORDER BY trade_date, stock_code"
        
        return pd.read_sql_query(query, self.connection, params=params)
    
    def search_stocks(self, keyword: str, trade_date: str = None) -> pd.DataFrame:
        """
        搜索股票
        
        Args:
            keyword: 关键词（股票代码或名称）
            trade_date: 交易日期（可选）
            
        Returns:
            DataFrame
        """
        query = "SELECT * FROM stock_daily WHERE (stock_code LIKE ? OR stock_name LIKE ?)"
        params = [f"%{keyword}%", f"%{keyword}%"]
        
        if trade_date:
            query += " AND trade_date = ?"
            params.append(trade_date)
        
        return pd.read_sql_query(query, self.connection, params=params)
    
    def get_all_dates(self) -> List[str]:
        """获取所有已导入的交易日期"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT trade_date FROM stock_daily ORDER BY trade_date DESC")
        return [row[0] for row in cursor.fetchall()]
    
    def get_all_sectors(self) -> List[str]:
        """获取所有板块"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT sector FROM stock_daily WHERE sector IS NOT NULL")
        sectors = set()
        for row in cursor.fetchall():
            if row[0]:
                # 板块可能是逗号分隔的多个板块
                for sector in str(row[0]).split('、'):
                    sectors.add(sector.strip())
        return sorted(list(sectors))
    
    def get_statistics(self, trade_date: str) -> Dict:
        """
        获取指定日期的统计信息
        
        Args:
            trade_date: 交易日期
            
        Returns:
            统计信息字典
        """
        cursor = self.connection.cursor()
        
        # 总股票数
        cursor.execute("SELECT COUNT(*) FROM stock_daily WHERE trade_date = ?", (trade_date,))
        total_count = cursor.fetchone()[0]
        
        # 主力净流入股票数
        cursor.execute(
            "SELECT COUNT(*) FROM stock_daily WHERE trade_date = ? AND main_net_amount > 0",
            (trade_date,)
        )
        positive_main_count = cursor.fetchone()[0]
        
        # 成交额增长股票数
        cursor.execute(
            "SELECT COUNT(*) FROM stock_daily WHERE trade_date = ? AND auction_today_volume > auction_yesterday_volume",
            (trade_date,)
        )
        positive_volume_count = cursor.fetchone()[0]
        
        # 平均换手率
        cursor.execute(
            "SELECT AVG(turnover_rate) FROM stock_daily WHERE trade_date = ? AND turnover_rate IS NOT NULL",
            (trade_date,)
        )
        avg_turnover = cursor.fetchone()[0] or 0
        
        return {
            'total_count': total_count,
            'positive_main_count': positive_main_count,
            'positive_volume_count': positive_volume_count,
            'avg_turnover': round(avg_turnover, 2)
        }
    
    def add_import_history(self, file_name: str, trade_date: str, 
                          records_count: int, status: str, 
                          error_message: str = None):
        """添加导入历史记录"""
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO import_history 
            (file_name, trade_date, records_count, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (file_name, trade_date, records_count, status, error_message))
        self.connection.commit()
    
    def get_import_history(self, limit: int = 100) -> pd.DataFrame:
        """获取导入历史"""
        return pd.read_sql_query(
            "SELECT * FROM import_history ORDER BY import_date DESC LIMIT ?",
            self.connection,
            params=[limit]
        )
    
    def delete_by_date(self, trade_date: str) -> int:
        """
        删除指定日期的数据
        
        Args:
            trade_date: 交易日期
            
        Returns:
            删除的行数
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM stock_daily WHERE trade_date = ?", (trade_date,))
        self.connection.commit()
        return cursor.rowcount
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logging.info("数据库连接已关闭")

