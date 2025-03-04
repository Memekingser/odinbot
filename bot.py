# -*- coding: utf-8 -*-
import os
import re
import json
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.request import Request
import logging

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取 Telegram Bot Token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("未找到 TELEGRAM_BOT_TOKEN 环境变量")
    raise ValueError("未找到 TELEGRAM_BOT_TOKEN 环境变量")

# 活跃群组文件路径
ACTIVE_GROUPS_FILE = 'active_groups.json'

# Bitcoin 价格（默认值）
DEFAULT_BTC_PRICE_USD = 83000

# 设置时区
timezone = pytz.timezone('Asia/Shanghai')

def get_btc_price():
    """获取 BTC 当前价格"""
    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
        if response.status_code == 200:
            data = response.json()
            return data['bitcoin']['usd']
        else:
            logger.warning(f"获取 BTC 价格失败，使用默认价格：${DEFAULT_BTC_PRICE_USD:,.2f}")
            return DEFAULT_BTC_PRICE_USD
    except Exception as e:
        logger.error(f"获取 BTC 价格时出错：{str(e)}")
        logger.warning(f"使用默认价格：${DEFAULT_BTC_PRICE_USD:,.2f}")
        return DEFAULT_BTC_PRICE_USD

def load_active_groups():
    """加载活跃群组列表"""
    if os.path.exists(ACTIVE_GROUPS_FILE):
        with open(ACTIVE_GROUPS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_active_groups(groups):
    """保存活跃群组列表"""
    with open(ACTIVE_GROUPS_FILE, 'w') as f:
        json.dump(groups, f)

def start(update: Update, context: CallbackContext):
    """处理 /start 命令"""
    logger.info(f"收到 /start 命令，来自用户 {update.effective_user.id}")
    
    # 如果是群组消息
    if update.effective_chat.type in ['group', 'supergroup']:
        chat_id = update.effective_chat.id
        active_groups = load_active_groups()
        
        # 如果群组不在活跃列表中，添加它
        if chat_id not in active_groups:
            active_groups.append(chat_id)
            save_active_groups(active_groups)
            update.message.reply_text('已激活群组消息查询功能！\n'
                                    '现在可以直接发送 Token 链接，我会自动查询并返回信息。')
        else:
            update.message.reply_text('该群组已经激活了消息查询功能！\n'
                                    '可以直接发送 Token 链接，我会自动查询并返回信息。')
    else:
        # 私聊消息
        update.message.reply_text('你好！我是一个 Token 信息查询机器人。\n'
                                '请将我添加到群组中，然后发送 /start 命令来激活群组消息查询功能。\n'
                                '激活后，可以直接发送类似 https://odin.fun/token/229u 的链接，'
                                '我会自动查询并返回该 Token 的最新信息。')

def handle_message(update: Update, context: CallbackContext):
    """处理消息"""
    logger.info(f"收到消息类型：{update.effective_chat.type}")
    
    # 检查是否是群组消息
    if update.effective_chat.type not in ['group', 'supergroup']:
        logger.info("不是群组消息，忽略")
        return
        
    # 检查群组是否在活跃列表中
    chat_id = update.effective_chat.id
    active_groups = load_active_groups()
    logger.info(f"当前活跃群组：{active_groups}")
    logger.info(f"当前群组 ID：{chat_id}")
    
    if chat_id not in active_groups:
        logger.info("群组未激活，忽略消息")
        return
        
    message = update.message.text
    logger.info(f"收到消息：{message}")
    
    # 使用更宽松的正则表达式匹配
    pattern = r'https://odin\.fun/token/([a-zA-Z0-9]+)'
    match = re.search(pattern, message)
    
    if match:
        token_id = match.group(1)
        logger.info(f"匹配到 token_id: {token_id}")
        try:
            # 获取当前时间戳
            timestamp = int(datetime.now().timestamp() * 1000)
            
            # 构建 API URL
            api_url = f'https://api.odin.fun/v1/token/{token_id}?timestamp={timestamp}'
            logger.info(f"请求 API: {api_url}")
            
            # 发送请求获取数据
            response = requests.get(api_url)
            logger.info(f"API 响应状态码: {response.status_code}")
            logger.info(f"API 响应内容: {response.text[:200]}...")  # 打印前200个字符
            
            if response.status_code == 200:
                data = response.json()
                
                # 获取当前 BTC 价格
                btc_price_usd = get_btc_price()
                
                # 计算价格（sats）和市值
                price_sats = data['price'] / 1000
                marketcap_btc = data['marketcap'] / 100000000000  # 除以 10000000000 再除以 10
                
                # 转换为 USD
                price_usd = price_sats * 0.00000001 * btc_price_usd
                marketcap_usd = marketcap_btc * btc_price_usd
                
                # 计算 dev 占比
                dev_percentage = (data['holder_dev'] / data['total_supply']) * 100
                
                # 计算价格涨跌幅
                price_5m = data['price_5m'] / 1000
                price_1h = data['price_1h'] / 1000
                price_6h = data['price_6h'] / 1000
                price_1d = data['price_1d'] / 1000
                
                # 计算价格变化百分比，添加错误处理
                def calculate_change(current, historical):
                    if historical == 0:
                        return 0.0
                    return ((current - historical) / historical) * 100
                
                change_5m = calculate_change(price_sats, price_5m)
                change_1h = calculate_change(price_sats, price_1h)
                change_6h = calculate_change(price_sats, price_6h)
                change_1d = calculate_change(price_sats, price_1d)
                
                # 计算运行时长
                created_time = datetime.strptime(data['created_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                created_time = created_time.replace(tzinfo=pytz.UTC).astimezone(timezone)
                now = datetime.now(timezone)
                running_time = now - created_time
                
                # 计算天数和小时数
                days = running_time.days
                hours = running_time.seconds // 3600
                
                # 构建回复消息
                reply_text = (
                    f"🔍 Token 信息查询\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📝 基本信息\n"
                    f"• 名称：{data['name']} ({data['ticker']})\n"
                    f"• 状态：{'✅ 已发射' if data['bonded'] else '⏳ 未发射'}\n"
                    f"• 开盘时间：{created_time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"• 运行时长：{days}天{hours}小时\n"
                    f"• 持有人数：{data['holder_count']:,}\n"
                    f"• Dev🥷占比：{dev_percentage:.2f}%\n\n"
                    f"💰 价格信息\n"
                    f"• 当前价格：{price_sats:.2f} sats (${price_usd:.4f})\n"
                    f"• 市值：${marketcap_usd:,.2f}\n\n"
                    f"📊 交易统计\n"
                    f"• 买入数🟢：{data['buy_count']:,} 次\n"
                    f"• 卖出数🔴：{data['sell_count']:,} 次\n\n"
                    f"📈 价格变化\n"
                    f"• 5分钟：{change_5m:+.2f}%\n"
                    f"• 1小时：{change_1h:+.2f}%\n"
                    f"• 6小时：{change_6h:+.2f}%\n"
                    f"• 24小时：{change_1d:+.2f}%"
                )
                
                # 添加社交媒体链接
                if data['twitter'] or data['telegram'] or data['website']:
                    reply_text += "\n\n🔗 相关链接"
                    if data['twitter']:
                        reply_text += f"\n• Twitter: {data['twitter']}"
                    if data['telegram']:
                        reply_text += f"\n• Telegram: {data['telegram']}"
                    if data['website']:
                        reply_text += f"\n• Website: {data['website']}"
                
                logger.info("发送回复消息")
                update.message.reply_text(reply_text)
            else:
                error_msg = f"API 请求失败，状态码：{response.status_code}"
                logger.error(error_msg)
                update.message.reply_text(error_msg)
            
        except Exception as e:
            logger.error(f"发生错误: {str(e)}")
            update.message.reply_text(f"获取 Token 信息时出错：{str(e)}")
    else:
        logger.info("消息格式不匹配")

def main():
    """主函数"""
    try:
        # 创建更新器
        logger.info("正在创建更新器...")
        updater = Updater(TOKEN, use_context=True)
        
        # 获取调度器
        dp = updater.dispatcher
        
        # 添加处理程序
        logger.info("正在添加处理程序...")
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # 启动机器人
        logger.info("机器人已启动...")
        logger.info(f"Bot Token: {TOKEN[:10]}...")  # 只打印 token 的前 10 个字符
        logger.info(f"已加载的活跃群组：{load_active_groups()}")
        
        # 开始轮询
        logger.info("开始轮询...")
        # 使用 443 端口
        port = 443
        # 启动 webhook 模式
        updater.start_webhook(
            listen='0.0.0.0',
            port=port,
            url_path=TOKEN
        )
        # 设置 webhook URL
        webhook_url = f'https://{os.getenv("RAILWAY_STATIC_URL")}/{TOKEN}'
        logger.info(f"设置 webhook URL: {webhook_url}")
        updater.bot.set_webhook(url=webhook_url)
        updater.idle()
    except Exception as e:
        logger.error(f"启动机器人时发生错误: {str(e)}")
        raise

if __name__ == '__main__':
    main() 
