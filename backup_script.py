#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动备份服务器资源脚本
"""

import os
import sys
import json
import time
import logging
import shutil
import threading
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict
import argparse

try:
    import paramiko
    from scp import SCPClient
except ImportError:
    print("请安装依赖: pip install paramiko scp")
    sys.exit(1)


class BackupConfig:
    """备份配置类"""
    
    def __init__(self, config_file: str = "backup_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            print(f"配置文件不存在: {self.config_file}")
            sys.exit(1)
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            sys.exit(1)


class IncrementalBackup:
    """增量备份管理类"""
    
    def __init__(self, server_name: str, backup_dir: Path):
        self.server_name = server_name
        self.backup_dir = backup_dir
        self.hash_index_dir = backup_dir / "hash_index"
        self.hash_index_dir.mkdir(exist_ok=True)
        self.hash_index_file = self.hash_index_dir / f"{server_name}_hash.json"
        self.hash_index = self.load_hash_index()
    
    def load_hash_index(self) -> Dict[str, str]:
        """加载哈希索引文件"""
        if not self.hash_index_file.exists():
            return {}
        
        try:
            with open(self.hash_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载哈希索引失败: {e}")
            return {}
    
    def save_hash_index(self):
        """保存哈希索引文件"""
        try:
            with open(self.hash_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.hash_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存哈希索引失败: {e}")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def get_remote_file_hash(self, remote_path: str, ssh_client) -> str:
        """获取远程文件哈希值"""
        try:
            stdin, stdout, stderr = ssh_client.exec_command(f'md5sum "{remote_path}"')
            result = stdout.read().decode('utf-8').strip()
            if result:
                return result.split()[0]
        except:
            pass
        return ""
    
    def get_remote_file_list(self, remote_path: str, ssh_client) -> list:
        """获取远程文件列表"""
        try:
            stdin, stdout, stderr = ssh_client.exec_command(f'find "{remote_path}" -type f')
            files = stdout.read().decode('utf-8').strip().split('\n')
            return [f for f in files if f.strip()]
        except:
            return []
    
    def should_backup_file(self, remote_path: str, ssh_client) -> bool:
        """判断文件是否需要备份"""
        # 获取远程文件哈希
        remote_hash = self.get_remote_file_hash(remote_path, ssh_client)
        if not remote_hash:
            return True  # 如果无法获取哈希，则备份
        
        # 获取之前的哈希
        previous_hash = self.hash_index.get(remote_path, "")
        
        # 如果哈希不同，则需要备份
        if remote_hash != previous_hash:
            self.hash_index[remote_path] = remote_hash
            return True
        
        return False
    
    def is_first_backup(self) -> bool:
        """判断是否是第一次备份"""
        return len(self.hash_index) == 0


class ProgressBar:
    """进度条显示类"""
    
    def __init__(self, total, description="进度", show_file_info=False):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.last_update = 0
        self.show_file_info = show_file_info
        self.current_file = ""
        self.total_size = 0
        self.transferred_size = 0
        self.last_size_update = 0
        
    def update(self, current, current_file="", file_size=0):
        """更新进度"""
        self.current = current
        if current_file:
            self.current_file = current_file
        if file_size > 0:
            self.transferred_size += file_size
            
        now = time.time()
        
        # 限制更新频率，避免刷屏
        if now - self.last_update < 0.1:
            return
            
        self.last_update = now
        
        # 计算进度百分比
        percent = (current / self.total) * 100 if self.total > 0 else 0
        
        # 计算速度
        elapsed = now - self.start_time
        speed = current / elapsed if elapsed > 0 else 0
        
        # 计算数据传输速度
        data_speed = self.transferred_size / elapsed if elapsed > 0 else 0
        
        # 计算剩余时间
        remaining = (self.total - current) / speed if speed > 0 else 0
        
        # 创建进度条
        bar_length = 30
        filled_length = int(bar_length * current // self.total) if self.total > 0 else 0
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # 格式化时间
        def format_time(seconds):
            if seconds < 60:
                return f"{seconds:.0f}秒"
            elif seconds < 3600:
                return f"{seconds/60:.0f}分{seconds%60:.0f}秒"
            else:
                return f"{seconds/3600:.0f}小时{(seconds%3600)/60:.0f}分"
        
        # 格式化文件大小
        def format_size(bytes_size):
            if bytes_size < 1024:
                return f"{bytes_size:.0f}B"
            elif bytes_size < 1024*1024:
                return f"{bytes_size/1024:.1f}KB"
            elif bytes_size < 1024*1024*1024:
                return f"{bytes_size/(1024*1024):.1f}MB"
            else:
                return f"{bytes_size/(1024*1024*1024):.1f}GB"
        
        # 格式化速度
        def format_speed(bytes_per_sec):
            if bytes_per_sec < 1024:
                return f"{bytes_per_sec:.0f}B/s"
            elif bytes_per_sec < 1024*1024:
                return f"{bytes_per_sec/1024:.1f}KB/s"
            elif bytes_per_sec < 1024*1024*1024:
                return f"{bytes_per_sec/(1024*1024):.1f}MB/s"
            else:
                return f"{bytes_per_sec/(1024*1024*1024):.1f}GB/s"
        
        # 构建显示信息
        info_parts = [
            f"{self.description}: |{bar}| {percent:.1f}% ({current}/{self.total})",
            f"速度: {speed:.1f}文件/秒",
            f"剩余: {format_time(remaining)}"
        ]
        
        # 添加数据传输信息
        if self.transferred_size > 0:
            info_parts.append(f"已传输: {format_size(self.transferred_size)}")
            info_parts.append(f"传输速度: {format_speed(data_speed)}")
        
        # 添加当前文件信息（如果启用）
        if self.show_file_info and self.current_file:
            # 截断过长的文件名
            display_file = self.current_file
            if len(display_file) > 50:
                display_file = "..." + display_file[-47:]
            info_parts.append(f"当前: {display_file}")
        
        # 显示进度条
        print(f"\r{' '.join(info_parts)}", end='', flush=True)
    
    def finish(self):
        """完成进度条"""
        elapsed = time.time() - self.start_time
        speed = self.total / elapsed if elapsed > 0 else 0
        data_speed = self.transferred_size / elapsed if elapsed > 0 else 0
        
        # 格式化函数
        def format_size(bytes_size):
            if bytes_size < 1024:
                return f"{bytes_size:.0f}B"
            elif bytes_size < 1024*1024:
                return f"{bytes_size/1024:.1f}KB"
            elif bytes_size < 1024*1024*1024:
                return f"{bytes_size/(1024*1024):.1f}MB"
            else:
                return f"{bytes_size/(1024*1024*1024):.1f}GB"
        
        def format_speed(bytes_per_sec):
            if bytes_per_sec < 1024:
                return f"{bytes_per_sec:.0f}B/s"
            elif bytes_per_sec < 1024*1024:
                return f"{bytes_per_sec/1024:.1f}KB/s"
            elif bytes_per_sec < 1024*1024*1024:
                return f"{bytes_per_sec/(1024*1024):.1f}MB/s"
            else:
                return f"{bytes_per_sec/(1024*1024*1024):.1f}GB/s"
        
        # 构建完成信息
        finish_info = [
            f"{self.description}: 完成!",
            f"总耗时: {elapsed:.1f}秒",
            f"平均速度: {speed:.1f}文件/秒"
        ]
        
        if self.transferred_size > 0:
            finish_info.append(f"总传输: {format_size(self.transferred_size)}")
            finish_info.append(f"平均传输速度: {format_speed(data_speed)}")
        
        print(f"\r{' '.join(finish_info)}")
        print()


class BackupLogger:
    """日志记录类"""
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        self.logger = logging.getLogger('BackupScript')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        
        # 文件处理器
        log_file = self.log_dir / f"backup_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        return self.logger


class SSHBackup:
    """SSH/SCP备份类"""
    
    def __init__(self, server_config: Dict, logger, incremental_backup, backup_settings=None):
        self.config = server_config
        self.logger = logger
        self.ssh_client = None
        self.scp_client = None
        self.total_files = 0
        self.copied_files = 0
        self.progress_bar = None
        self.monitor_thread = None
        self.is_downloading = False
        self.incremental_backup = incremental_backup
        self.backup_settings = backup_settings or {}
    
    def connect(self) -> bool:
        """建立SSH连接"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.config['host'],
                port=self.config.get('port', 22),
                username=self.config['username'],
                password=self.config['password'],
                timeout=30
            )
            
            self.scp_client = SCPClient(self.ssh_client.get_transport())
            self.logger.info(f"SSH连接成功: {self.config['host']}")
            return True
            
        except Exception as e:
            self.logger.error(f"SSH连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.scp_client:
            self.scp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
    
    def get_remote_file_count(self, remote_path: str) -> int:
        """获取远程目录文件数量"""
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(f'find {remote_path} -type f | wc -l')
            result = stdout.read().decode('utf-8').strip()
            return int(result) if result.isdigit() else 0
        except:
            return 0
    
    def get_local_file_count(self, local_path: str) -> int:
        """获取本地目录文件数量"""
        try:
            count = 0
            for root, dirs, files in os.walk(local_path):
                count += len(files)
            return count
        except:
            return 0
    
    def get_remote_file_size(self, remote_path: str) -> int:
        """获取远程文件大小"""
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(f'stat -c%s "{remote_path}"')
            result = stdout.read().decode('utf-8').strip()
            return int(result) if result.isdigit() else 0
        except:
            return 0
    
    def monitor_progress(self, local_path: str):
        """监控下载进度"""
        while self.is_downloading:
            try:
                current_files = self.get_local_file_count(local_path)
                if self.progress_bar and current_files <= self.total_files:
                    self.progress_bar.update(current_files)
                time.sleep(0.5)  # 每0.5秒更新一次
            except:
                break
    
    def download_directory(self, remote_path: str, local_path: str) -> bool:
        """智能备份目录（第一次全量，后续增量）"""
        try:
            os.makedirs(local_path, exist_ok=True)
            
            # 判断是否是第一次备份
            is_first_backup = self.incremental_backup.is_first_backup()
            
            if is_first_backup:
                # 第一次备份：全量备份
                print(f"\n开始全量备份目录: {remote_path}")
                print("这是第一次备份，将下载所有文件")
                print("=" * 50)
                
                # 获取文件总数
                self.total_files = self.get_remote_file_count(remote_path)
                
                if self.total_files > 0:
                    # 创建进度条（全量备份不显示文件名，因为SCP是批量传输）
                    self.progress_bar = ProgressBar(self.total_files, "全量备份", show_file_info=False)
                    self.is_downloading = True
                    
                    # 启动进度监控线程
                    self.monitor_thread = threading.Thread(target=self.monitor_progress, args=(local_path,))
                    self.monitor_thread.daemon = True
                    self.monitor_thread.start()
                
                # 使用SCP全量下载
                self.scp_client.get(remote_path, local_path, recursive=True)
                
                # 停止进度监控
                self.is_downloading = False
                if self.monitor_thread:
                    self.monitor_thread.join(timeout=1)
                
                if self.progress_bar:
                    self.progress_bar.finish()
                
                # 第一次备份后，建立哈希索引
                self.build_hash_index_after_full_backup(remote_path, local_path)
                
                print(f"全量备份完成: {remote_path}")
                print(f"备份文件数量: {self.total_files}")
                
            else:
                # 后续备份：增量备份
                remote_files = self.incremental_backup.get_remote_file_list(remote_path, self.ssh_client)
                
                # 筛选需要备份的文件
                files_to_backup = []
                for file_path in remote_files:
                    if self.incremental_backup.should_backup_file(file_path, self.ssh_client):
                        files_to_backup.append(file_path)
                
                total_files = len(remote_files)
                backup_files = len(files_to_backup)
                
                print(f"\n开始增量备份目录: {remote_path}")
                print(f"总文件数量: {total_files}")
                print(f"需要备份: {backup_files} 个文件")
                print(f"跳过文件: {total_files - backup_files} 个文件")
                print("=" * 50)
                
                if backup_files == 0:
                    print("所有文件都是最新的，无需备份")
                    return True
                
                # 创建进度条（根据配置决定是否显示文件信息）
                show_file_info = self.backup_settings.get('show_current_file', True)
                self.progress_bar = ProgressBar(backup_files, "增量备份", show_file_info=show_file_info)
                self.copied_files = 0
                
                # 逐个下载需要备份的文件
                for i, file_path in enumerate(files_to_backup):
                    try:
                        # 计算相对路径
                        rel_path = os.path.relpath(file_path, remote_path)
                        local_file_path = os.path.join(local_path, rel_path)
                        
                        # 确保本地目录存在
                        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                        
                        # 获取远程文件大小
                        file_size = self.get_remote_file_size(file_path)
                        
                        # 下载单个文件
                        self.scp_client.get(file_path, local_file_path)
                        
                        self.copied_files += 1
                        # 更新进度条，包含当前文件名和文件大小
                        self.progress_bar.update(self.copied_files, file_path, file_size)
                        
                    except Exception as e:
                        print(f"\n文件下载失败 {file_path}: {e}")
                        # 即使失败也要更新进度条
                        self.copied_files += 1
                        self.progress_bar.update(self.copied_files, file_path, 0)
                        continue
                
                if self.progress_bar:
                    self.progress_bar.finish()
                
                print(f"增量备份完成: {remote_path}")
                print(f"实际备份文件: {self.copied_files}/{backup_files}")
            
            # 保存哈希索引
            self.incremental_backup.save_hash_index()
            return True
            
        except Exception as e:
            # 停止进度监控
            self.is_downloading = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=1)
            
            print(f"\n备份失败 {remote_path}: {e}")
            return False
    
    def build_hash_index_after_full_backup(self, remote_path: str, local_path: str):
        """全量备份后建立哈希索引"""
        print("正在建立文件索引...")
        
        # 获取远程文件列表
        remote_files = self.incremental_backup.get_remote_file_list(remote_path, self.ssh_client)
        
        # 为每个文件建立哈希索引
        for file_path in remote_files:
            remote_hash = self.incremental_backup.get_remote_file_hash(file_path, self.ssh_client)
            if remote_hash:
                self.incremental_backup.hash_index[file_path] = remote_hash
        
        print(f"已建立 {len(remote_files)} 个文件的索引")


class BackupManager:
    """备份管理器"""
    
    def __init__(self, config_file: str = "backup_config.json"):
        self.config = BackupConfig(config_file)
        self.logger = BackupLogger().get_logger()
        
        # 创建备份目录
        self.backup_dir = Path(self.config.config['backup_settings']['local_backup_dir'])
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_server(self, server_config: Dict) -> bool:
        """备份单个服务器"""
        server_name = server_config['name']
        print(f"\n开始备份服务器: {server_name}")
        print(f"服务器地址: {server_config['host']}")
        print(f"用户名: {server_config['username']}")
        print("=" * 60)
        
        self.logger.info(f"开始备份服务器: {server_name}")
        
        # 创建服务器备份目录 - 使用固定的基础目录进行增量备份
        server_backup_dir = self.backup_dir / server_name / "current"
        server_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建版本备份目录（用于保留历史版本）
        version_backup_dir = self.backup_dir / server_name / datetime.now().strftime('%Y%m%d_%H%M%S')
        version_backup_dir.mkdir(parents=True, exist_ok=True)
        
        success = True
        total_paths = len(server_config['remote_paths'])
        
        try:
            # 创建增量备份管理器 - 使用服务器目录而不是根备份目录
            server_dir = self.backup_dir / server_name
            incremental_backup = IncrementalBackup(server_name, server_dir)
            backup_client = SSHBackup(server_config, self.logger, incremental_backup, self.config.config['backup_settings'])
            
            # 建立连接
            print("正在连接服务器...")
            if not backup_client.connect():
                print("连接失败")
                return False
            
            print("连接成功")
            
            # 备份每个路径
            for i, remote_path in enumerate(server_config['remote_paths'], 1):
                print(f"\n备份路径 {i}/{total_paths}: {remote_path}")
                
                # 生成本地路径
                local_path = server_backup_dir / remote_path.lstrip('/')
                
                # 下载目录
                if backup_client.download_directory(remote_path, str(local_path)):
                    print(f"路径备份成功: {remote_path}")
                    self.logger.info(f"路径备份成功: {remote_path}")
                else:
                    print(f"路径备份失败: {remote_path}")
                    self.logger.error(f"路径备份失败: {remote_path}")
                    success = False
            
            backup_client.disconnect()
            print("连接已断开")
            
        except Exception as e:
            print(f"服务器备份异常: {e}")
            self.logger.error(f"服务器备份异常: {e}")
            success = False
        
        if success:
            # 将当前备份复制到版本目录（用于版本管理）
            try:
                print("正在创建备份版本...")
                self.copy_backup_to_version(server_backup_dir, version_backup_dir)
                print(f"备份版本已创建: {version_backup_dir.name}")
            except Exception as e:
                print(f" 创建备份版本失败: {e}")
                self.logger.warning(f"创建备份版本失败: {e}")
            
            print(f"\n服务器备份完成: {server_name}")
            print(f"当前备份位置: {server_backup_dir}")
            print(f"版本备份位置: {version_backup_dir}")
            self.logger.info(f"服务器备份完成: {server_name}")
            self.cleanup_old_backups(server_name)
        else:
            print(f"\n服务器备份失败: {server_name}")
            self.logger.error(f"服务器备份失败: {server_name}")
            # 删除失败的版本目录
            try:
                if version_backup_dir.exists():
                    shutil.rmtree(version_backup_dir)
            except:
                pass
        
        return success
    
    def copy_backup_to_version(self, source_dir: Path, target_dir: Path):
        """将当前备份复制到版本目录"""
        try:
            # 如果目标目录已存在，先删除
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            # 复制整个目录
            shutil.copytree(source_dir, target_dir)
            self.logger.info(f"备份版本已创建: {target_dir}")
            
        except Exception as e:
            self.logger.error(f"复制备份到版本目录失败: {e}")
            raise
    
    def cleanup_old_backups(self, server_name: str):
        """清理旧备份，保留指定数量的版本"""
        max_versions = self.config.config['backup_settings']['max_backup_versions']
        server_dir = self.backup_dir / server_name
        
        if not server_dir.exists():
            return
        
        # 获取所有版本备份目录（排除current目录），按时间排序
        backup_dirs = [d for d in server_dir.iterdir() if d.is_dir() and d.name != "current"]
        backup_dirs.sort(key=lambda x: x.name, reverse=True)
        
        # 删除超出限制的备份版本
        for old_backup in backup_dirs[max_versions:]:
            try:
                shutil.rmtree(old_backup)
                self.logger.info(f"删除旧备份版本: {old_backup}")
            except Exception as e:
                self.logger.error(f"删除旧备份版本失败 {old_backup}: {e}")
    
    def run_backup(self):
        """执行备份任务"""
        print("=" * 60)
        print("自动备份任务开始")
        print("=" * 60)
        
        self.logger.info("开始执行备份任务")
        start_time = time.time()
        
        success_count = 0
        total_count = len(self.config.config['servers'])
        
        print(f"总共需要备份 {total_count} 个服务器")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        for i, server_config in enumerate(self.config.config['servers'], 1):
            print(f"\n进度: {i}/{total_count}")
            if self.backup_server(server_config):
                success_count += 1
                print(f"服务器 {i} 备份成功")
            else:
                print(f"服务器 {i} 备份失败")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("备份任务完成")
        print("=" * 60)
        print(f"成功: {success_count}/{total_count}")
        print(f"失败: {total_count - success_count}/{total_count}")
        print(f"总耗时: {duration:.2f} 秒")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if success_count == total_count:
            print("所有服务器备份成功！")
        else:
            print("部分服务器备份失败，请检查日志")
        
        self.logger.info(f"备份任务完成: {success_count}/{total_count} 成功，耗时 {duration:.2f} 秒")
        
        return success_count == total_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='自动备份服务器资源脚本')
    parser.add_argument('--config', '-c', default='backup_config.json', help='配置文件路径')
    parser.add_argument('--server', '-s', help='指定要备份的服务器名称')
    parser.add_argument('--test', '-t', action='store_true', help='测试模式，只检查配置')
    
    args = parser.parse_args()
    
    try:
        backup_manager = BackupManager(args.config)
        
        if args.test:
            print("配置测试模式")
            print(f"找到 {len(backup_manager.config.config['servers'])} 个服务器配置")
            for server in backup_manager.config.config['servers']:
                print(f"- {server['name']} ({server['protocol']}://{server['host']})")
            return
        
        if args.server:
            # 备份指定服务器
            server_config = None
            for server in backup_manager.config.config['servers']:
                if server['name'] == args.server:
                    server_config = server
                    break
            
            if server_config:
                backup_manager.backup_server(server_config)
            else:
                print(f"未找到服务器: {args.server}")
        else:
            # 备份所有服务器
            backup_manager.run_backup()
    
    except KeyboardInterrupt:
        print("\n备份任务被用户中断")
    except Exception as e:
        print(f"备份任务执行失败: {e}")


if __name__ == "__main__":
    main()