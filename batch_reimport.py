"""批量重新导入工具 - 清空数据库并重新导入所有Excel文件"""
import sys
import os
import logging
from pathlib import Path
from database import DatabaseManager
from data_processor import ExcelParser
import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_reimport.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

sys.stdout.reconfigure(encoding='utf-8')

def confirm_action(message):
    """确认操作"""
    print(f"\n⚠️  {message}")
    response = input("确认执行? (yes/no): ").strip().lower()
    return response == 'yes'

def batch_import_directory(db_manager, directory_path):
    """批量导入目录下的所有Excel文件"""
    
    # 查找所有Excel文件
    excel_files = []
    directory = Path(directory_path)
    
    for pattern in ['*.xlsx', '*.xls']:
        excel_files.extend(directory.glob(pattern))
    
    # 按文件名排序
    excel_files = sorted(excel_files)
    
    if not excel_files:
        print(f"❌ 在目录 {directory_path} 中没有找到Excel文件")
        return
    
    print(f"\n找到 {len(excel_files)} 个Excel文件:")
    for i, file in enumerate(excel_files, 1):
        print(f"  {i:2d}. {file.name}")
    
    if not confirm_action(f"即将导入 {len(excel_files)} 个文件，继续吗？"):
        print("已取消")
        return
    
    # 统计
    success_count = 0
    fail_count = 0
    total_records = 0
    
    print(f"\n开始批量导入...\n")
    
    for i, file_path in enumerate(excel_files, 1):
        try:
            print(f"[{i}/{len(excel_files)}] 处理: {file_path.name}")
            
            # 解析Excel
            df, trade_date = ExcelParser.parse_excel(str(file_path), config.COLUMN_MAPPING)
            
            # 插入数据
            inserted, skipped = db_manager.insert_batch(df, trade_date)
            
            print(f"  ✅ 成功导入 {inserted} 条, 跳过 {skipped} 条")
            
            success_count += 1
            total_records += inserted
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            fail_count += 1
            logging.error(f"导入失败: {file_path.name}, 错误: {e}", exc_info=True)
    
    print(f"\n{'='*80}")
    print(f"批量导入完成！")
    print(f"{'='*80}")
    print(f"  成功文件: {success_count}")
    print(f"  失败文件: {fail_count}")
    print(f"  总记录数: {total_records:,}")
    print(f"{'='*80}\n")

def main():
    """主函数"""
    print("\n" + "="*80)
    print("批量重新导入工具")
    print("="*80)
    
    # 可选：清空整个数据库
    if len(sys.argv) > 1 and sys.argv[1] == '--clear':
        if confirm_action("这将删除数据库中的所有数据！"):
            db_manager = DatabaseManager(config.DB_PATH)
            cursor = db_manager.connection.cursor()
            cursor.execute("DELETE FROM stock_daily")
            deleted = cursor.rowcount
            db_manager.connection.commit()
            print(f"✅ 已删除 {deleted:,} 条旧数据\n")
        else:
            print("已取消清空操作")
            return
    
    # 初始化数据库
    db_manager = DatabaseManager(config.DB_PATH)
    
    # 显示当前数据库统计
    cursor = db_manager.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock_daily")
    current_count = cursor.fetchone()[0]
    print(f"\n当前数据库记录数: {current_count:,}")
    
    cursor.execute("SELECT MIN(trade_date), MAX(trade_date) FROM stock_daily")
    date_range = cursor.fetchone()
    if date_range[0]:
        print(f"日期范围: {date_range[0]} 到 {date_range[1]}")
    
    # 选择导入目录
    print(f"\n请选择要导入的目录:")
    print(f"1. 2025-10 目录（根目录）")
    print(f"2. sample_data 目录（测试数据）")
    print(f"3. 自定义目录")
    print(f"4. 退出")
    
    choice = input(f"\n请选择 (1-4): ").strip()
    
    if choice == '1':
        directory = '../2025-10'
    elif choice == '2':
        directory = 'sample_data'
    elif choice == '3':
        directory = input("请输入目录路径: ").strip()
    else:
        print("已退出")
        return
    
    # 检查目录是否存在
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return
    
    # 批量导入
    batch_import_directory(db_manager, directory)
    
    # 显示最终统计
    cursor.execute("SELECT COUNT(*) FROM stock_daily")
    final_count = cursor.fetchone()[0]
    print(f"\n最终数据库记录数: {final_count:,}")
    
    cursor.execute("SELECT COUNT(DISTINCT trade_date) FROM stock_daily")
    date_count = cursor.fetchone()[0]
    print(f"包含交易日数: {date_count}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()

