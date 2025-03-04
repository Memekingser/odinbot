# Token 信息查询 Telegram 机器人

这是一个 Telegram 机器人，可以自动查询 Odin.fun 上的 Token 信息。

## 功能特点

- 自动检测群组中的 Token 链接
- 实时查询 Token 价格、市值等信息
- 支持 24 小时价格变化追踪
- 显示持有人数量等关键信息

## 安装步骤

1. 克隆项目到本地
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 复制 `.env.example` 文件为 `.env`：
   ```bash
   cp .env.example .env
   ```
4. 在 `.env` 文件中设置你的 Telegram Bot Token
5. 运行机器人：
   ```bash
   python bot.py
   ```

## 使用方法

1. 将机器人添加到你的 Telegram 群组
2. 在群组中发送类似 `@https://odin.fun/token/229u` 的消息
3. 机器人会自动回复该 Token 的详细信息

## 注意事项

- 确保机器人具有群组消息的读取权限
- 建议将机器人设置为群组管理员，以确保其能正常接收所有消息 