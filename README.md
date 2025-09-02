# Python聊天软件

一个基于WebSocket的简单聊天软件，包含图形界面客户端和服务器端。

## 功能特性

- 🖥️ 图形化用户界面（基于tkinter）
- 🔧 可配置服务器IP和端口
- 🔒 支持HTTP和HTTPS协议
- 👤 用户名和唯一ID管理
- 💬 实时群聊功能
- 🔒 一对一私聊功能
- ☁️ 基于腾讯云COS的云端聊天
- 📁 基于网络共享目录的企业聊天
- 🔐 Base64双重加密保护聊天记录
- 📎 文件和图片传输功能
- 👥 在线用户列表
- 📝 系统消息提示
- 🔔 私聊消息提醒
- 💾 聊天记录持久化存储
- 🧹 自动清理机制

## 安装依赖

### 方法1：使用系统包管理器（推荐）
```bash
sudo apt update
sudo apt install python3-websockets python3-tk
```

### 方法2：使用pip（需要虚拟环境）
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 方法3：安装COS聊天依赖
```bash
python3 install_cos_dependencies.py
```

## 使用方法

### 1. 启动服务器

#### HTTP模式（默认）
```bash
python3 chat_server.py
```

#### 自定义主机和端口
```bash
python3 chat_server.py --host 0.0.0.0 --port 8080
```

#### HTTPS模式（需要SSL证书）
```bash
python3 chat_server.py --ssl --cert server.crt --key server.key
```

### 2. 启动客户端

```bash
python3 chat_client.py
```

### 3. 使用图形化启动器（推荐）

```bash
python3 start_server.py
```

### 4. 运行演示

```bash
python3 demo.py
```

### 5. 使用客户端

#### WebSocket模式（实时聊天）
1. **配置服务器**：
   - 输入服务器地址（默认：localhost）
   - 输入端口号（默认：8765）
   - 选择协议（HTTP或HTTPS）

2. **设置用户信息**：
   - 输入用户名
   - 用户ID会自动生成，也可以手动修改

3. **连接和聊天**：
   - 点击"连接"按钮连接到服务器
   - 在输入框中输入消息，按回车或点击"发送"进行群聊
   - 查看在线用户列表
   - 双击用户列表中的用户名开始一对一私聊

#### COS云端模式（云存储聊天）
```bash
python3 cos_chat_client.py
```

1. **配置COS**：
   - 输入腾讯云Secret ID和Secret Key
   - 输入Bucket名称和Region
   - 设置聊天室路径

2. **云端聊天**：
   - 消息存储在腾讯云COS上
   - 每3秒自动同步新消息
   - 支持群聊和私聊
   - 聊天记录持久化保存

#### 网络共享目录模式（企业内网聊天）
```bash
python3 network_share_chat.py
```

1. **配置共享目录**：
   - 设置网络共享路径：`\\catl-tfile\Temp1day每天凌晨两点清理数据01\imdmmm`
   - 测试目录访问权限
   - 输入用户名和用户ID

2. **企业聊天**：
   - 消息存储在网络共享目录
   - 所有聊天记录使用Base64双重加密
   - 每3秒自动扫描新消息
   - 支持群聊和私聊
   - 支持文件和图片传输（最大50MB）
   - 每天凌晨2点自动清理旧数据

## 服务器命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 服务器绑定地址 | localhost |
| `--port` | 服务器端口 | 8765 |
| `--ssl` | 启用HTTPS/WSS | 关闭 |
| `--cert` | SSL证书文件路径 | 无 |
| `--key` | SSL私钥文件路径 | 无 |

## 生成SSL证书（用于HTTPS测试）

```bash
# 生成自签名证书（仅用于测试）
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
```

## 架构说明

### 服务器端 (`chat_server.py`)
- 基于`websockets`库实现WebSocket服务器
- 支持HTTP和HTTPS协议
- 管理用户连接和消息广播
- 用户ID唯一性验证
- 实时在线用户列表更新

### 客户端 (`chat_client.py`)
- 基于`tkinter`的图形界面
- 异步WebSocket连接处理
- 服务器配置界面
- 实时消息显示和发送
- 在线用户列表显示

## 消息协议

### 客户端到服务器
```json
{
  "type": "join",
  "user_id": "用户ID",
  "username": "用户名"
}

{
  "type": "chat",
  "user_id": "用户ID",
  "username": "用户名",
  "message": "消息内容"
}

{
  "type": "private_chat",
  "user_id": "发送者ID",
  "username": "发送者用户名",
  "target_user_id": "接收者ID",
  "message": "消息内容"
}
```

### 服务器到客户端
```json
{
  "type": "chat",
  "user_id": "用户ID",
  "username": "用户名",
  "message": "消息内容",
  "timestamp": "时间戳"
}

{
  "type": "private_chat",
  "user_id": "发送者ID",
  "username": "发送者用户名",
  "target_user_id": "接收者ID",
  "message": "消息内容",
  "timestamp": "时间戳"
}

{
  "type": "user_joined",
  "user_id": "用户ID",
  "username": "用户名",
  "online_users": ["用户列表"]
}
```

## 注意事项

1. **用户ID唯一性**：每个用户必须有唯一的ID，重复ID会被拒绝连接
2. **HTTPS证书**：生产环境请使用有效的SSL证书
3. **防火墙**：确保服务器端口未被防火墙阻止
4. **网络**：客户端需要能够访问服务器的IP和端口

## 故障排除

1. **连接失败**：检查服务器是否运行，IP和端口是否正确
2. **用户ID冲突**：更改用户ID为唯一值
3. **HTTPS连接问题**：检查证书文件路径和权限
4. **消息发送失败**：检查网络连接状态

## 扩展功能

## 聊天功能使用说明

### WebSocket实时聊天
1. **开始私聊**：双击在线用户列表中的任意用户名
2. **私聊窗口**：每个私聊对象都有独立的聊天窗口
3. **消息提醒**：收到新私聊消息时窗口标题会显示提醒
4. **窗口管理**：可以同时打开多个私聊窗口

### COS云端聊天
1. **配置要求**：需要腾讯云COS账号和访问密钥
2. **消息存储**：所有聊天记录存储在COS指定目录
3. **同步机制**：每3秒自动检查新消息
4. **持久化**：聊天记录永久保存在云端
5. **跨设备**：可在不同设备间同步聊天记录

### 网络共享目录聊天
1. **配置要求**：需要访问指定的网络共享目录
2. **消息存储**：聊天记录存储在 `\\catl-tfile\Temp1day每天凌晨两点清理数据01\imdmmm`
3. **加密安全**：所有消息使用Base64双重加密，硬编码密钥保护
4. **文件传输**：支持文档、图片等文件传输，最大50MB
5. **同步机制**：每3秒扫描共享目录获取新消息
6. **自动清理**：每天凌晨2点自动清理旧数据
7. **企业适用**：适合企业内网环境，无需外网连接

#### 支持的文件类型：
- **文档**：.txt, .doc, .docx, .pdf, .xls, .xlsx, .ppt, .pptx
- **图片**：.jpg, .jpeg, .png, .gif, .bmp, .webp
- **压缩包**：.zip, .rar, .7z, .tar, .gz
- **媒体**：.mp3, .mp4, .avi, .mov

#### 目录结构：
```
\\catl-tfile\Temp1day每天凌晨两点清理数据01\imdmmm\
├── public/          # 群聊消息（加密）
├── private/         # 私聊消息（加密）
├── files/           # 文件存储
├── images/          # 图片存储
├── thumbnails/      # 图片缩略图
├── users/           # 用户心跳
└── logs/            # 清理日志
```

## 其他可扩展功能

- 消息历史搜索
- 更多文件类型支持
- 图片预览和缩略图
- 表情符号支持
- 用户头像功能
- 聊天室分组管理
- 更强的加密算法
- 离线消息推送
- 文件版本管理
- 批量文件下载