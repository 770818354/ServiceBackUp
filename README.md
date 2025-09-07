# 服务器增量备份工具

一个功能强大的服务器自动备份工具，支持SSH/SCP协议，采用智能增量备份机制，大幅提升备份效率。

## 特性

- **智能增量备份**: 首次全量备份，后续只备份有变化的文件
- **实时进度显示**: 详细的备份进度条和传输速度显示
- **版本管理**: 自动保留多个历史版本，支持版本回滚
- **定时备份**: 支持自定义备份时间，自动执行备份任务
- **安全可靠**: 支持SSH密钥认证，确保数据传输安全
- **详细日志**: 完整的备份日志记录，便于问题排查
-  **灵活配置**: 支持多服务器、多路径、排除规则等配置

## 快速开始

### 1. 环境要求

- Python 3.6+
- Windows/Linux/macOS

### 2. 安装依赖

**Windows:**
```bash
install.bat
```

**Linux/macOS:**
```bash
pip install -r requirements.txt
```

### 3. 配置服务器

编辑 `backup_config.json` 文件，配置你的服务器信息：

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
                "/var/www/html",
                "/home/user/data",
                "/etc/nginx"
            ],
            "exclude_patterns": [
                "*.log",
                "*.tmp",
                "__pycache__",
                ".git",
                "node_modules",
                "*.cache"
            ]
        }
    ],
    "backup_settings": {
        "local_backup_dir": "./backups",
        "max_backup_versions": 7,
        "compression": true,
        "encryption": false,
        "log_level": "INFO",
        "show_detailed_progress": true,
        "show_current_file": true
    },
    "schedule": {
        "enabled": true,
        "interval_hours": 6,
        "backup_times": ["09:00", "12:00", "17:00", "00:00"]
    }
}
```

### 4. 使用脚本

**手动备份所有服务器：**
```bash
python backup_script.py
```

**备份指定服务器：**
```bash
python backup_script.py --server "我的Web服务器"
```

**测试配置：**
```bash
python backup_script.py --test
```

**启动定时备份：**
```bash
python schedule_backup.py
```

**检查配置：**
```bash
python check_config.py
```

## 项目结构

```
ServiceBackUp/
├── backup_script.py          # 主备份脚本
├── schedule_backup.py        # 定时任务脚本
├── check_config.py          # 配置检查脚本
├── backup_config.json       # 配置文件
├── requirements.txt         # Python依赖
├── install.bat             # Windows安装脚本
├── backup.bat              # Windows备份脚本
├── schedule.bat            # Windows定时脚本
├── start_backup.bat        # Windows启动脚本
├── logs/                   # 日志目录
└── backups/                # 备份文件目录
    └── 服务器名称/
        ├── current/        # 当前备份（增量基础）
        ├── 20240101_090000/ # 版本备份1
        ├── 20240101_120000/ # 版本备份2
        └── hash_index/     # 文件哈希索引
```

## 配置说明

### 服务器配置

| 参数 | 说明 | 示例 |
|------|------|------|
| `name` | 服务器名称 | "我的Web服务器" |
| `host` | 服务器IP或域名 | "192.168.1.100" |
| `port` | SSH端口 | 22 |
| `username` | 用户名 | "root" |
| `password` | 密码 | "your-password" |
| `protocol` | 协议类型 | "ssh" |
| `remote_paths` | 要备份的远程路径 | ["/var/www/html"] |
| `exclude_patterns` | 排除的文件模式 | ["*.log", "*.tmp"] |

### 备份设置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `local_backup_dir` | 本地备份目录 | "./backups" |
| `max_backup_versions` | 最大保留版本数 | 7 |
| `compression` | 是否压缩 | true |
| `encryption` | 是否加密 | false |
| `log_level` | 日志级别 | "INFO" |
| `show_detailed_progress` | 显示详细进度 | true |
| `show_current_file` | 显示当前文件 | true |

### 定时设置

| 参数 | 说明 | 示例 |
|------|------|------|
| `enabled` | 是否启用定时备份 | true |
| `interval_hours` | 备份间隔（小时） | 6 |
| `backup_times` | 备份时间点 | ["09:00", "12:00"] |

## 备份机制

### 增量备份原理

1. **首次备份**: 全量下载所有文件到 `current` 目录
2. **建立索引**: 为每个文件计算MD5哈希值，建立文件索引
3. **增量备份**: 比较远程文件哈希与本地索引，只下载有变化的文件
4. **版本管理**: 每次备份完成后创建时间戳版本快照
5. **自动清理**: 保留指定数量的历史版本，删除过期版本

### 备份目录结构

```
backups/
└── 服务器名称/
    ├── current/              # 增量备份基础目录
    │   ├── var/
    │   │   └── www/
    │   │       └── html/
    │   └── home/
    │       └── user/
    │           └── data/
    ├── 20240101_090000/      # 版本备份1
    ├── 20240101_120000/      # 版本备份2
    └── hash_index/           # 文件哈希索引
        └── 服务器名称_hash.json
```

## 使用示例

### 基本使用

```bash
# 备份所有服务器
python backup_script.py

# 备份指定服务器
python backup_script.py --server "我的Web服务器"

# 测试配置
python backup_script.py --test
```

### 定时备份

```bash
# 启动定时备份服务
python schedule_backup.py
```

### Windows批处理

```bash
# 安装依赖
install.bat

# 执行备份
backup.bat

# 启动定时备份
schedule.bat
```

## 🛠️ 高级功能

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

### 排除规则配置

```json
{
    "exclude_patterns": [
        "*.log",           # 排除日志文件
        "*.tmp",           # 排除临时文件
        "__pycache__",     # 排除Python缓存
        ".git",            # 排除Git目录
        "node_modules",    # 排除Node.js依赖
        "*.cache",         # 排除缓存文件
        "*.bak"            # 排除备份文件
    ]
}
```

## 日志说明

日志文件保存在 `logs/` 目录下，按日期命名：
- `backup_20240101.log` - 备份日志
- `schedule.log` - 定时任务日志

日志包含详细的备份信息：
- 连接状态
- 文件传输进度
- 错误信息
- 备份统计

## 注意事项

1. **密码安全**: 建议使用SSH密钥认证替代密码认证
2. **网络稳定**: 确保网络连接稳定，避免备份中断
3. **磁盘空间**: 确保本地有足够的磁盘空间存储备份文件
4. **权限设置**: 确保有足够的权限访问远程目录
5. **防火墙**: 确保SSH端口（默认22）未被防火墙阻止

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
