# 快速开始指南

## 🚀 5分钟快速上手

### 1. 克隆或下载项目
```bash
git clone <your-repo-url>
cd ServiceBackUp
```

### 2. 安装依赖
**Windows:**
```bash
install.bat
```

**Linux/macOS:**
```bash
pip install -r requirements.txt
```

### 3. 配置服务器信息
复制示例配置文件：
```bash
# Windows
copy backup_config.example.json backup_config.json

# Linux/macOS
cp backup_config.example.json backup_config.json
```

编辑 `backup_config.json`，修改以下信息：
- `host`: 你的服务器IP地址
- `username`: SSH用户名
- `password`: SSH密码
- `remote_paths`: 要备份的目录路径

### 4. 测试配置
```bash
python check_config.py
```

### 5. 执行备份
```bash
# 手动备份
python backup_script.py

# 或使用批处理文件（Windows）
backup.bat
```

### 6. 启动定时备份（可选）
```bash
# 启动定时备份服务
python schedule_backup.py

# 或使用批处理文件（Windows）
schedule.bat
```

## 配置示例

### 基本配置
```json
{
    "servers": [
        {
            "name": "我的Web服务器",
            "host": "192.168.1.100",
            "port": 22,
            "username": "root",
            "password": "your-password",
            "protocol": "ssh",
            "remote_paths": [
                "/var/www/html"
            ]
        }
    ],
    "backup_settings": {
        "local_backup_dir": "./backups",
        "max_backup_versions": 7
    }
}
```

### 多服务器配置
```json
{
    "servers": [
        {
            "name": "Web服务器",
            "host": "192.168.1.100",
            "username": "root",
            "password": "password1",
            "remote_paths": ["/var/www/html"]
        },
        {
            "name": "数据库服务器",
            "host": "192.168.1.101",
            "username": "mysql",
            "password": "password2",
            "remote_paths": ["/var/lib/mysql"]
        }
    ]
}
```

## 🔧 常用命令

```bash
# 备份所有服务器
python backup_script.py

# 备份指定服务器
python backup_script.py --server "服务器名称"

# 测试配置
python backup_script.py --test

# 检查配置
python check_config.py

# 启动定时备份
python schedule_backup.py
```

## 备份文件位置

备份文件保存在 `./backups/` 目录下：
```
backups/
└── 服务器名称/
    ├── current/              # 当前备份（增量基础）
    ├── 20240101_090000/      # 版本备份1
    ├── 20240101_120000/      # 版本备份2
    └── hash_index/           # 文件哈希索引
```

## 常见问题

### Q: 如何修改备份时间？
A: 编辑 `backup_config.json` 中的 `backup_times` 数组：
```json
"backup_times": ["09:00", "12:00", "17:00", "00:00"]
```

### Q: 如何排除某些文件？
A: 在 `exclude_patterns` 中添加排除规则：
```json
"exclude_patterns": ["*.log", "*.tmp", "__pycache__"]
```

### Q: 如何查看备份日志？
A: 日志文件保存在 `logs/` 目录下，按日期命名。

### Q: 如何停止定时备份？
A: 按 `Ctrl+C` 停止定时备份服务。

## 🆘 获取帮助

如果遇到问题，请：
1. 查看日志文件 `logs/backup_*.log`
2. 运行 `python check_config.py` 检查配置
3. 运行 `python backup_script.py --test` 测试连接
4. 查看完整的 [README.md](README.md) 文档
