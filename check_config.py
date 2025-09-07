#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置检查脚本
"""

import json
import os

def check_config():
    """检查配置文件"""
    print("=" * 40)
    print("配置检查")
    print("=" * 40)
    
    if not os.path.exists('backup_config.json'):
        print("配置文件不存在: backup_config.json")
        return False
    
    try:
        with open('backup_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("配置文件格式正确")
        
        # 检查服务器配置
        servers = config.get('servers', [])
        if not servers:
            print("没有配置服务器")
            return False
        
        print(f"找到 {len(servers)} 个服务器")
        
        for i, server in enumerate(servers, 1):
            print(f"\n服务器 {i}: {server.get('name', '未命名')}")
            print(f"  主机: {server.get('host', '未设置')}")
            print(f"  用户: {server.get('username', '未设置')}")
            print(f"  协议: {server.get('protocol', '未设置')}")
            print(f"  备份路径: {len(server.get('remote_paths', []))} 个")
        
        # 检查定时设置
        schedule = config.get('schedule', {})
        if schedule.get('enabled'):
            if 'backup_times' in schedule:
                times = schedule['backup_times']
                print(f"\n定时备份: 每天 {len(times)} 次")
                print(f"  时间: {', '.join(times)}")
            else:
                print(f"\n定时备份: 每天 1 次")
        else:
            print("\n定时备份已禁用")
        
        print("\n配置检查完成")
        return True
        
    except Exception as e:
        print(f"配置检查失败: {e}")
        return False

if __name__ == "__main__":
    check_config()
