"""
Excel数据解析模块
"""
import os
import re
import logging
from datetime import datetime
from typing import Tuple, Optional
import pandas as pd
import openpyxl


class ExcelParser:
    """Excel文件解析器"""
    
    @staticmethod
    def extract_date_from_filename(filename: str) -> Optional[str]:
        """
        从文件名提取日期
        
        Args:
            filename: 文件名，例如 "2025-09-01.xlsx" 或 "2025-09-01-5142.xlsx"
            
        Returns:
            日期字符串 "YYYY-MM-DD" 或 None
        """
        # 提取YYYY-MM-DD格式的日期
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        # 尝试提取YYYY/MM/DD格式
        match = re.search(r'(\d{4})[/\\](\d{2})[/\\](\d{2})', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        return None
    
    @staticmethod
    def parse_excel(file_path: str, column_mapping: dict = None) -> Tuple[pd.DataFrame, str]:
        """
        解析Excel文件
        
        Args:
            file_path: Excel文件路径
            column_mapping: 列名映射字典
            
        Returns:
            (DataFrame, 交易日期)
        """
        try:
            # 读取Excel文件
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_path.endswith('.xls'):
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                raise ValueError(f"不支持的文件格式: {file_path}")
            
            filename = os.path.basename(file_path)
            
            # 🔍 详细日志：打印Excel原始信息
            logging.info(f"\n{'='*80}")
            logging.info(f"📁 开始解析Excel文件: {filename}")
            logging.info(f"{'='*80}")
            logging.info(f"📊 Excel数据形状: {df.shape[0]} 行 × {df.shape[1]} 列")
            logging.info(f"📋 Excel列名列表（共{len(df.columns)}列）:")
            for i, col in enumerate(df.columns, 1):
                logging.info(f"    {i:2d}. {col}")
            
            # 打印第一行数据作为样本
            if len(df) > 0:
                logging.info(f"\n💡 第一行数据示例:")
                for col in df.columns[:10]:  # 只显示前10列
                    value = df[col].iloc[0]
                    logging.info(f"    {col}: {value}")
                if len(df.columns) > 10:
                    logging.info(f"    ... (还有 {len(df.columns)-10} 列)")
            
            # 从文件名提取日期
            trade_date = ExcelParser.extract_date_from_filename(filename)
            
            if not trade_date:
                logging.warning(f"⚠️  无法从文件名提取日期: {filename}")
                # 尝试从数据中获取日期
                if '交易日期' in df.columns:
                    first_date = df['交易日期'].iloc[0]
                    if pd.notna(first_date):
                        trade_date = str(first_date).split()[0]
                        logging.info(f"✓ 从数据列中获取日期: {trade_date}")
            else:
                logging.info(f"✓ 从文件名提取日期: {trade_date}")
            
            # 数据标准化
            df_normalized = ExcelParser._normalize_data(df, column_mapping, filename)
            
            logging.info(f"\n✅ Excel解析完成: {filename}")
            logging.info(f"   - 导入记录数: {len(df_normalized)}")
            logging.info(f"   - 交易日期: {trade_date}")
            logging.info(f"{'='*80}\n")
            
            return df_normalized, trade_date
            
        except Exception as e:
            logging.error(f"❌ 解析Excel失败: {file_path}")
            logging.error(f"   错误信息: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _normalize_data(df: pd.DataFrame, column_mapping: dict = None, filename: str = "") -> pd.DataFrame:
        """
        数据标准化处理
        
        Args:
            df: 原始DataFrame
            column_mapping: 列名映射
            filename: 文件名（用于日志）
            
        Returns:
            标准化后的DataFrame
        """
        if column_mapping is None:
            column_mapping = {}
        
        logging.info(f"\n🔄 开始列名映射...")
        
        # 创建新的DataFrame
        normalized_df = pd.DataFrame()
        
        # 记录映射情况
        mapped_count = 0
        unmapped_excel_cols = []
        
        # ✅ 修复：遍历Excel的每一列，而不是遍历配置文件
        for excel_col in df.columns:
            if excel_col in column_mapping:
                db_col = column_mapping[excel_col]
                # 如果目标列还没有数据，才进行映射（避免重复映射覆盖）
                if db_col not in normalized_df.columns:
                    normalized_df[db_col] = df[excel_col].copy()
                    logging.info(f"    ✓ 映射: '{excel_col}' -> '{db_col}'")
                    mapped_count += 1
                else:
                    logging.info(f"    ⚠️  跳过: '{excel_col}' -> '{db_col}' (目标列已存在)")
            else:
                unmapped_excel_cols.append(excel_col)
        
        # 记录未映射的列
        if unmapped_excel_cols:
            logging.warning(f"\n⚠️  以下Excel列未配置映射（将被忽略）:")
            for col in unmapped_excel_cols:
                logging.warning(f"    - {col}")
        
        logging.info(f"\n📊 列映射统计:")
        logging.info(f"    - Excel总列数: {len(df.columns)}")
        logging.info(f"    - 成功映射: {mapped_count} 列")
        logging.info(f"    - 未映射: {len(unmapped_excel_cols)} 列")
        logging.info(f"    - 结果列数: {len(normalized_df.columns)}")
        
        # 数据清洗
        logging.info(f"\n🧹 开始数据清洗...")
        normalized_df = ExcelParser._clean_data(normalized_df)
        
        # 打印清洗后的示例数据
        if len(normalized_df) > 0:
            logging.info(f"\n💾 清洗后的数据示例（第一行）:")
            for col in normalized_df.columns[:10]:
                value = normalized_df[col].iloc[0]
                logging.info(f"    {col}: {value}")
            if len(normalized_df.columns) > 10:
                logging.info(f"    ... (还有 {len(normalized_df.columns)-10} 列)")
        
        return normalized_df
    
    @staticmethod
    def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗
        
        Args:
            df: DataFrame
            
        Returns:
            清洗后的DataFrame
        """
        # 处理股票代码（确保是6位字符串，前导零）
        if 'stock_code' in df.columns:
            df['stock_code'] = df['stock_code'].apply(
                lambda x: str(int(x)).zfill(6) if pd.notna(x) and str(x).replace('.', '').isdigit() else str(x)
            )
        
        # 处理数值字段，移除"万"、"亿"等单位
        numeric_columns = [
            'current_price', 'price_change', 'auction_net_amount', 'auction_main_net',
            'auction_today_volume', 'auction_yesterday_volume',
            'main_net_amount', 'real_market_value', 'main_net_ratio', 'flow_ratio',
            'net_ratio', 'buy_sell_ratio', 'turnover_rate', 'real_turnover_rate',
            'volume_ratio', 'popularity_value', 'popularity_change'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(ExcelParser._parse_numeric)
        
        # 处理竞价增额字段（保留原始文本，如 "2+", "3+", "5+"）
        if 'auction_increase' in df.columns:
            df['auction_increase'] = df['auction_increase'].astype(str).replace('nan', '')
        
        return df
    
    @staticmethod
    def _parse_numeric(value) -> Optional[float]:
        """
        解析数值（处理带单位的数值，如"1000万"、"1.2亿"）
        
        Args:
            value: 原始值
            
        Returns:
            浮点数或None
        """
        if pd.isna(value) or value == '' or value is None:
            return None
        
        try:
            # 如果已经是数值类型
            if isinstance(value, (int, float)):
                return float(value)
            
            # 字符串处理
            str_value = str(value).strip()
            original_value = str_value  # 保存原始值用于日志
            
            # 处理亿单位（1亿 = 10000万）
            if '亿' in str_value:
                str_value = str_value.replace('亿', '').replace(',', '').strip()
                if str_value and str_value != '-':
                    result = float(str_value) * 10000  # 转换为万
                    # logging.debug(f"    数值转换: '{original_value}' -> {result} (亿转万)")
                    return result
            
            # 处理万单位
            if '万' in str_value:
                str_value = str_value.replace('万', '').replace(',', '').strip()
                if str_value and str_value != '-':
                    result = float(str_value)
                    # logging.debug(f"    数值转换: '{original_value}' -> {result}")
                    return result
            
            # 移除其他常见符号
            str_value = str_value.replace(',', '').replace('%', '').strip()
            
            # 处理空字符串
            if not str_value or str_value == '-':
                return None
            
            result = float(str_value)
            # logging.debug(f"    数值转换: '{original_value}' -> {result}")
            return result
            
        except (ValueError, TypeError) as e:
            logging.warning(f"    ⚠️  无法解析数值: '{value}' (类型: {type(value).__name__})")
            return None
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> Tuple[bool, str]:
        """
        验证数据完整性
        
        Args:
            df: DataFrame
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查必要列
        required_columns = ['stock_code', 'stock_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"缺少必要列: {', '.join(missing_columns)}"
        
        # 检查是否有数据
        if len(df) == 0:
            return False, "Excel文件中没有数据"
        
        # 检查股票代码是否有效
        invalid_codes = df[df['stock_code'].isna() | (df['stock_code'] == '')]
        if len(invalid_codes) > 0:
            return False, f"存在无效的股票代码，共 {len(invalid_codes)} 条"
        
        return True, "数据验证通过"

