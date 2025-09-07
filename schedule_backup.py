#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时备份调度脚本
"""

import os
import sys
import time
import schedule
import logging
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backup_script import BackupManager


class ScheduleManager:
    """定时任务管理器"""
    
    def __init__(self, config_file: str = "backup_config.json"):
        self.config_file = config_file
        self.logger = self.setup_logger()
        self.backup_manager = BackupManager(config_file)
    
    def setup_logger(self):
        """设置日志记录器"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('schedule.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def run_backup_job(self):
        """执行备份任务"""
        self.logger.info("定时备份任务开始执行")
        try:
            success = self.backup_manager.run_backup()
            if success:
                self.logger.info("定时备份任务执行成功")
            else:
                self.logger.error("定时备份任务执行失败")
        except Exception as e:
            self.logger.error(f"定时备份任务执行异常: {e}")
    
    def start_scheduler(self):
        """启动定时调度器"""
        config = self.backup_manager.config.config
        
        if not config['schedule']['enabled']:
            self.logger.info("定时备份已禁用")
            return
        
        # 设置备份时间
        if 'backup_times' in config['schedule']:
            # 支持多个备份时间
            backup_times = config['schedule']['backup_times']
            for backup_time in backup_times:
                schedule.every().day.at(backup_time).do(self.run_backup_job)
            self.logger.info(f"定时备份已设置，每天执行 {len(backup_times)} 次: {', '.join(backup_times)}")
        else:
            # 兼容旧的单个备份时间配置
            backup_time = config['schedule']['backup_time']
            schedule.every().day.at(backup_time).do(self.run_backup_job)
            self.logger.info(f"定时备份已设置，每天 {backup_time} 执行")
        
        # 保持程序运行
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次




def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='定时备份调度器')
    parser.add_argument('--config', '-c', default='backup_config.json', help='配置文件路径')
    parser.add_argument('--run-once', action='store_true', help='立即执行一次备份')
    
    args = parser.parse_args()
    
    if args.run_once:
        # 立即执行一次备份
        backup_manager = BackupManager(args.config)
        backup_manager.run_backup()
        return
    
    # 启动定时调度器
    scheduler = ScheduleManager(args.config)
    scheduler.start_scheduler()


if __name__ == "__main__":
    main()