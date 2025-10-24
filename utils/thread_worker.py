"""
多线程工具模块
"""
from PyQt5.QtCore import QThread, pyqtSignal
import logging


class WorkerThread(QThread):
    """
    通用工作线程
    """
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # (进度百分比, 消息)
    task_completed = pyqtSignal(object)  # 任务完成，返回结果
    task_failed = pyqtSignal(str)  # 任务失败，返回错误信息
    
    def __init__(self, task_func, *args, **kwargs):
        """
        初始化工作线程
        
        Args:
            task_func: 要执行的函数
            *args, **kwargs: 函数参数
        """
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """执行任务"""
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.task_completed.emit(result)
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            logging.error(error_msg)
            self.task_failed.emit(error_msg)


class BatchImportWorker(QThread):
    """
    批量导入工作线程
    """
    # 信号定义
    progress_updated = pyqtSignal(int, int, str)  # (当前文件索引, 总文件数, 当前文件名)
    file_imported = pyqtSignal(str, int, bool, str)  # (文件名, 记录数, 成功/失败, 消息)
    all_completed = pyqtSignal(int, int, int)  # (成功数, 失败数, 总记录数)
    
    def __init__(self, file_paths, db_manager, excel_parser, column_mapping):
        """
        初始化批量导入线程
        
        Args:
            file_paths: 文件路径列表
            db_manager: 数据库管理器
            excel_parser: Excel解析器
            column_mapping: 列名映射
        """
        super().__init__()
        self.file_paths = file_paths
        self.db_manager = db_manager
        self.excel_parser = excel_parser
        self.column_mapping = column_mapping
        self._is_running = True
    
    def stop(self):
        """停止线程"""
        self._is_running = False
    
    def run(self):
        """执行批量导入"""
        total_files = len(self.file_paths)
        success_count = 0
        fail_count = 0
        total_records = 0
        
        for idx, file_path in enumerate(self.file_paths):
            if not self._is_running:
                break
            
            try:
                # 发送进度信号
                import os
                filename = os.path.basename(file_path)
                self.progress_updated.emit(idx + 1, total_files, filename)
                
                # 解析Excel
                df, trade_date = self.excel_parser.parse_excel(file_path, self.column_mapping)
                
                if trade_date is None:
                    raise ValueError("无法提取交易日期")
                
                # 插入数据库
                inserted, skipped = self.db_manager.insert_batch(df, trade_date)
                
                # 记录导入历史
                self.db_manager.add_import_history(
                    filename, trade_date, inserted, 'success', None
                )
                
                # 发送文件导入完成信号
                self.file_imported.emit(
                    filename, inserted, True, 
                    f"成功导入 {inserted} 条，跳过 {skipped} 条"
                )
                
                success_count += 1
                total_records += inserted
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"导入文件失败: {file_path}, 错误: {error_msg}")
                
                # 记录导入历史
                try:
                    self.db_manager.add_import_history(
                        filename, None, 0, 'failed', error_msg
                    )
                except:
                    pass
                
                # 发送文件导入失败信号
                self.file_imported.emit(filename, 0, False, error_msg)
                fail_count += 1
        
        # 发送全部完成信号
        self.all_completed.emit(success_count, fail_count, total_records)

