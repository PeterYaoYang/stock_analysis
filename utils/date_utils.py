"""
日期工具模块
"""
from datetime import datetime, timedelta
from typing import List


def format_date(date_obj) -> str:
    """
    格式化日期为 YYYY-MM-DD
    
    Args:
        date_obj: 日期对象（datetime, str等）
        
    Returns:
        格式化后的日期字符串
    """
    if isinstance(date_obj, str):
        return date_obj
    elif isinstance(date_obj, datetime):
        return date_obj.strftime('%Y-%m-%d')
    else:
        return str(date_obj)


def parse_date(date_str: str) -> datetime:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串
        
    Returns:
        datetime对象
    """
    # 尝试多种格式
    formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"无法解析日期: {date_str}")


def get_date_range(start_date: str, end_date: str) -> List[str]:
    """
    获取日期范围内的所有日期
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        日期列表
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return dates


def get_recent_dates(days: int = 30) -> List[str]:
    """
    获取最近N天的日期
    
    Args:
        days: 天数
        
    Returns:
        日期列表
    """
    today = datetime.now()
    dates = []
    
    for i in range(days):
        date = today - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
    
    return dates

