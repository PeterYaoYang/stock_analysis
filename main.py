"""
股票数据分析系统 - 主程序
"""
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from ui.main_window import MainWindow


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('stock_analysis.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """主函数"""
    # 配置日志
    setup_logging()
    logging.info("=" * 50)
    logging.info("股票数据分析系统启动")
    logging.info("=" * 50)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("股票数据分析系统")
    
    # 设置全局字体
    font = QFont("微软雅黑", 10)
    app.setFont(font)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    try:
        main_window = MainWindow()
        main_window.show()
        
        logging.info("主窗口已显示")
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        logging.error(f"程序运行失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

