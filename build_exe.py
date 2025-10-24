"""
打包脚本 - 将程序打包成exe
"""
import os
import sys


def build():
    """打包程序"""
    print("=" * 60)
    print("开始打包股票数据分析系统...")
    print("=" * 60)
    
    # PyInstaller打包命令
    cmd = """
    pyinstaller --noconfirm ^
        --onefile ^
        --windowed ^
        --name="股票数据分析系统" ^
        --icon=resources/icon.ico ^
        --add-data="config.py;." ^
        main.py
    """
    
    # 如果没有图标文件，不添加icon参数
    if not os.path.exists("resources/icon.ico"):
        cmd = """
        pyinstaller --noconfirm ^
            --onefile ^
            --windowed ^
            --name="股票数据分析系统" ^
            --add-data="config.py;." ^
            main.py
        """
    
    print("\n执行打包命令...")
    print(cmd)
    print("\n")
    
    os.system(cmd)
    
    print("\n" + "=" * 60)
    print("打包完成！")
    print("=" * 60)
    print("\n可执行文件位置: dist/股票数据分析系统.exe")
    print("\n使用说明:")
    print("1. 将 dist/股票数据分析系统.exe 复制到任意文件夹")
    print("2. 双击运行即可")
    print("3. 程序会在同目录下自动创建 stock_data.db 数据库文件")
    print("4. 可以将整个文件夹（含数据库）发给其他人使用")


if __name__ == '__main__':
    # 检查是否安装了PyInstaller
    try:
        import PyInstaller
        build()
    except ImportError:
        print("错误: 未安装 PyInstaller")
        print("请先运行: pip install pyinstaller")
        sys.exit(1)

