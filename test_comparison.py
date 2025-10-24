"""测试前日对比功能"""
import sys
import logging
from database import DatabaseManager
import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("测试前日对比功能")
print("=" * 80)

# 初始化数据库
db = DatabaseManager(config.DB_PATH)

# 获取所有日期
all_dates = db.get_all_dates()
print(f"\n数据库中的交易日期（共{len(all_dates)}个）:")
for i, date in enumerate(all_dates[:5], 1):
    print(f"  {i}. {date}")
if len(all_dates) > 5:
    print(f"  ... 还有 {len(all_dates) - 5} 个日期")

# 测试1：获取前一个交易日
if len(all_dates) >= 2:
    current_date = all_dates[0]
    print(f"\n【测试1】获取前一个交易日")
    print(f"当前日期: {current_date}")
    
    prev_date = db._get_previous_trade_date(current_date)
    print(f"前一个交易日: {prev_date}")
    
    if prev_date == all_dates[1]:
        print("✅ 前一个交易日获取正确")
    else:
        print(f"❌ 前一个交易日不正确，预期: {all_dates[1]}")

# 测试2：查询带对比的数据
if len(all_dates) >= 2:
    test_date = all_dates[0]
    print(f"\n【测试2】查询带前日对比的数据")
    print(f"查询日期: {test_date}")
    
    try:
        df = db.query_by_date_with_comparison(test_date, limit=10)
        
        print(f"✅ 查询成功，返回 {len(df)} 条数据")
        
        # 检查新列是否存在
        if 'main_net_prev_ratio' in df.columns:
            print("✅ 'main_net_prev_ratio' 列存在")
        else:
            print("❌ 'main_net_prev_ratio' 列不存在")
        
        if 'volume_prev_ratio' in df.columns:
            print("✅ 'volume_prev_ratio' 列存在")
        else:
            print("❌ 'volume_prev_ratio' 列不存在")
        
        # 显示前5条数据
        print(f"\n前5条数据示例:")
        print(f"{'股票代码':<10} {'股票名称':<12} {'主力净额':<12} {'主力净额对比':<15} {'成交额':<12} {'成交额对比':<15}")
        print("-" * 90)
        
        for idx, row in df.head(5).iterrows():
            code = row['stock_code']
            name = row['stock_name'][:10] if len(str(row['stock_name'])) > 10 else row['stock_name']
            main_net = row.get('main_net_amount', 0)
            main_ratio = row.get('main_net_prev_ratio')
            volume = row.get('auction_today_volume', 0)
            vol_ratio = row.get('volume_prev_ratio')
            
            main_net_str = f"{main_net:.1f}" if main_net else "N/A"
            main_ratio_str = f"{main_ratio:.2f}x" if main_ratio else "-"
            volume_str = f"{volume:.1f}" if volume else "N/A"
            vol_ratio_str = f"{vol_ratio:.2f}x" if vol_ratio else "-"
            
            print(f"{code:<10} {name:<12} {main_net_str:<12} {main_ratio_str:<15} {volume_str:<12} {vol_ratio_str:<15}")
        
        # 统计对比值
        main_ratios = df['main_net_prev_ratio'].dropna()
        vol_ratios = df['volume_prev_ratio'].dropna()
        
        print(f"\n对比值统计:")
        print(f"  主力净额对比:")
        print(f"    - 有效数据: {len(main_ratios)}/{len(df)} 条")
        if len(main_ratios) > 0:
            print(f"    - 平均值: {main_ratios.mean():.2f}x")
            print(f"    - 最大值: {main_ratios.max():.2f}x")
            print(f"    - 最小值: {main_ratios.min():.2f}x")
        
        print(f"  成交额对比:")
        print(f"    - 有效数据: {len(vol_ratios)}/{len(df)} 条")
        if len(vol_ratios) > 0:
            print(f"    - 平均值: {vol_ratios.mean():.2f}x")
            print(f"    - 最大值: {vol_ratios.max():.2f}x")
            print(f"    - 最小值: {vol_ratios.min():.2f}x")
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()

# 测试3：检查默认排序
if len(all_dates) >= 1:
    test_date = all_dates[0]
    print(f"\n【测试3】检查默认排序（按股票代码正序）")
    print(f"查询日期: {test_date}")
    
    try:
        df = db.query_by_date_with_comparison(test_date, limit=10)
        
        stock_codes = df['stock_code'].tolist()
        print(f"前10个股票代码: {stock_codes}")
        
        # 检查是否按升序排列
        is_sorted = all(stock_codes[i] <= stock_codes[i+1] for i in range(len(stock_codes)-1))
        
        if is_sorted:
            print("✅ 股票代码按升序排列")
        else:
            print("❌ 股票代码未按升序排列")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

# 测试4：测试UI格式化函数
print(f"\n【测试4】测试UI格式化函数")
from ui.data_table_view import DataTableView

view = DataTableView()

test_ratios = [
    (0.5, "减少50%"),
    (0.8, "减少20%"),
    (1.0, "持平"),
    (1.2, "增加20%"),
    (1.5, "增加50%"),
    (2.0, "翻倍"),
    (3.5, "3.5倍"),
]

print(f"\n对比值格式化测试:")
print(f"{'原始值':<15} {'格式化后':<15} {'说明':<20}")
print("-" * 50)

for value, desc in test_ratios:
    formatted = view._format_ratio(value)
    print(f"{value:<15.2f} {formatted:<15} {desc:<20}")

print("\n✅ 所有测试完成！")
print("\n现在可以启动GUI程序查看实际效果：")
print("  python main.py")
print("  或双击 run.bat")

