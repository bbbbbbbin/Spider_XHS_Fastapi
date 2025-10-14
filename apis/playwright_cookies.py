# encoding: utf-8
"""
使用Playwright自动获取小红书游客cookies
"""

import json
import time
from playwright.sync_api import sync_playwright
from loguru import logger

class XHSCookieGetter:
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        初始化Cookie获取器
        :param headless: 是否无头模式
        :param timeout: 超时时间(毫秒)
        """
        self.headless = headless
        self.timeout = timeout
        
    def get_guest_cookies(self, wait_time: int = 5, retry_count: int = 3):
        """
        获取小红书游客cookies
        :param wait_time: 等待页面加载时间(秒)
        :param retry_count: 重试次数
        :return: (success, cookies_str, cookies_dict)
        """
        for attempt in range(retry_count):
            try:
                logger.info(f"🔄 第 {attempt + 1} 次尝试获取cookies...")
                
                with sync_playwright() as p:
                    # 启动浏览器
                    browser = p.chromium.launch(
                        headless=self.headless,
                        args=[
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-accelerated-2d-canvas',
                            '--no-first-run',
                            '--no-zygote',
                            '--disable-gpu'
                        ]
                    )
                    
                    # 创建上下文
                    context = browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
                    )
                    
                    # 创建页面
                    page = context.new_page()
                    
                    # 设置超时
                    page.set_default_timeout(self.timeout)
                    
                    logger.info("🌐 正在访问小红书首页...")
                    
                    # 访问小红书首页
                    response = page.goto('https://www.xiaohongshu.com', wait_until='networkidle')
                    
                    if response.status != 200:
                        logger.warning(f"⚠️  页面响应状态码: {response.status}")
                    
                    # 等待页面完全加载
                    logger.info(f"⏳ 等待页面加载 {wait_time} 秒...")
                    time.sleep(wait_time)
                    
                    # 尝试等待一些关键元素加载
                    try:
                        page.wait_for_selector('body', timeout=10000)
                        logger.info("✅ 页面基本元素已加载")
                    except:
                        logger.warning("⚠️  未检测到页面基本元素，继续尝试获取cookies")
                    
                    # 获取cookies
                    cookies = context.cookies()
                    
                    if not cookies:
                        logger.warning("⚠️  未获取到任何cookies")
                        browser.close()
                        continue
                    
                    # 转换cookies格式
                    cookies_dict = {}
                    cookies_list = []
                    
                    for cookie in cookies:
                        cookies_dict[cookie['name']] = cookie['value']
                        cookies_list.append(f"{cookie['name']}={cookie['value']}")
                    
                    cookies_str = "; ".join(cookies_list)
                    
                    # 检查关键cookies
                    required_cookies = ['webId', 'xsecappid']
                    missing_cookies = [name for name in required_cookies if name not in cookies_dict]
                    
                    if missing_cookies:
                        logger.warning(f"⚠️  缺少关键cookies: {missing_cookies}")
                    
                    logger.info(f"✅ 成功获取 {len(cookies)} 个cookies")
                    logger.info(f"📏 Cookies字符串长度: {len(cookies_str)}")
                    
                    # 打印主要cookies（调试用）
                    main_cookies = ['webId', 'xsecappid', 'webBuild', 'abRequestId']
                    logger.info("🔍 主要cookies:")
                    for name in main_cookies:
                        if name in cookies_dict:
                            value = cookies_dict[name]
                            display_value = value[:20] + "..." if len(value) > 20 else value
                            logger.info(f"   {name}: {display_value}")
                    
                    browser.close()
                    return True, cookies_str, cookies_dict
                    
            except Exception as e:
                logger.error(f"❌ 第 {attempt + 1} 次尝试失败: {str(e)}")
                if attempt < retry_count - 1:
                    logger.info(f"🔄 {3} 秒后重试...")
                    time.sleep(3)
                else:
                    logger.error("❌ 所有尝试都失败了")
        
        return False, "", {}
    
    def get_cookies_with_browser_interaction(self, manual_wait: bool = False):
        """
        获取cookies（支持手动浏览器交互）
        :param manual_wait: 是否等待手动操作
        :return: (success, cookies_str, cookies_dict)
        """
        try:
            logger.info("🖥️  启动可视化浏览器获取cookies...")
            
            with sync_playwright() as p:
                # 启动可视化浏览器
                browser = p.chromium.launch(
                    headless=False,  # 显示浏览器
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
                )
                
                page = context.new_page()
                
                logger.info("🌐 正在打开小红书首页...")
                page.goto('https://www.xiaohongshu.com')
                
                if manual_wait:
                    logger.info("⏸️  浏览器已打开，你可以手动操作（如登录）")
                    input("完成操作后按回车键继续获取cookies...")
                else:
                    logger.info("⏳ 等待页面自动加载...")
                    time.sleep(5)
                
                # 获取cookies
                cookies = context.cookies()
                cookies_dict = {}
                cookies_list = []
                
                for cookie in cookies:
                    cookies_dict[cookie['name']] = cookie['value']
                    cookies_list.append(f"{cookie['name']}={cookie['value']}")
                
                cookies_str = "; ".join(cookies_list)
                
                logger.info(f"✅ 获取到 {len(cookies)} 个cookies")
                
                browser.close()
                return True, cookies_str, cookies_dict
                
        except Exception as e:
            logger.error(f"❌ 可视化获取cookies失败: {str(e)}")
            return False, "", {}
    
    def save_cookies(self, cookies_dict: dict, file_path: str = "auto_cookies.json"):
        """
        保存cookies到文件
        :param cookies_dict: cookies字典
        :param file_path: 保存路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cookies_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Cookies已保存到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 保存cookies失败: {str(e)}")
            return False
    
    def load_cookies(self, file_path: str = "auto_cookies.json"):
        """
        从文件加载cookies
        :param file_path: 文件路径
        :return: (success, cookies_str, cookies_dict)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cookies_dict = json.load(f)
            
            cookies_list = [f"{k}={v}" for k, v in cookies_dict.items()]
            cookies_str = "; ".join(cookies_list)
            
            logger.info(f"📂 从文件加载了 {len(cookies_dict)} 个cookies")
            return True, cookies_str, cookies_dict
            
        except FileNotFoundError:
            logger.warning(f"⚠️  文件不存在: {file_path}")
            return False, "", {}
        except Exception as e:
            logger.error(f"❌ 加载cookies失败: {str(e)}")
            return False, "", {}

def test_cookie_getter():
    """
    测试cookie获取功能
    """
    print("🧪 测试Playwright获取cookies功能")
    print("=" * 50)
    
    getter = XHSCookieGetter(headless=True)
    
    # 测试自动获取
    print("1️⃣  测试自动获取游客cookies...")
    success, cookies_str, cookies_dict = getter.get_guest_cookies()
    
    if success:
        print("✅ 自动获取成功!")
        print(f"📊 获取到 {len(cookies_dict)} 个cookies")
        print(f"📏 Cookies字符串长度: {len(cookies_str)}")
        
        # 保存cookies
        # getter.save_cookies(cookies_dict, "test_cookies.json")
        
        # 显示部分cookies
        print("\n🔍 部分cookies内容:")
        for i, (name, value) in enumerate(list(cookies_dict.items())[:5]):
            display_value = value[:30] + "..." if len(value) > 30 else value
            print(f"   {name}: {display_value}")
        
        return 200, cookies_str
    else:
        print("❌ 自动获取失败")
        return None

if __name__ == "__main__":
    test_cookie_getter()