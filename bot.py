# ... existing code ...

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
        if PROXY_URL:
            logger.info(f"使用代理：{PROXY_URL}")
        
        # 开始轮询
        logger.info("开始轮询...")
        # 获取 PORT 环境变量
        port = int(os.getenv('PORT', 8000))
        # 启动 webhook 模式
        updater.start_webhook(
            listen='0.0.0.0',
            port=port,
            url_path=TOKEN
        )
        # 设置 webhook URL
        updater.bot.set_webhook(url=f'https://{os.getenv("RAILWAY_STATIC_URL")}/{TOKEN}')
        updater.idle()
    except Exception as e:
        logger.error(f"启动机器人时发生错误: {str(e)}")
        raise

# ... existing code ...
