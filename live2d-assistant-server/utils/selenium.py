import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import WebDriverException
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class WebDriverManager:
    """
    WebDriver管理器类,用于创建和管理WebDriver实例
    支持with语法进行上下文管理
    """
    def __init__(self):
        self.driver = None
        
    def __enter__(self):
        self.driver = self.create_webdriver()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_webdriver()

    def check_browser_availability(self):
        """
        检查当前系统可用的浏览器
        返回: (driver_class, options_class, service_class, browser_path) 或 None
        """
        system = platform.system()
        
        if system == "Windows":
            browsers = {
                "edge": {
                    "paths": [
                        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                        "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
                    ],
                    "driver": (webdriver.Edge, EdgeOptions, EdgeService)
                },
                "chrome": {
                    "paths": [
                        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                    ],
                    "driver": (webdriver.Chrome, ChromeOptions, ChromeService)
                },
                "firefox": {
                    "paths": [
                        "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                        "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
                    ],
                    "driver": (webdriver.Firefox, FirefoxOptions, FirefoxService)
                }
            }
        elif system == "Darwin":  # macOS
            browsers = {
                "edge": {
                    "paths": [
                        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
                    ],
                    "driver": (webdriver.Edge, EdgeOptions, EdgeService)
                },
                "chrome": {
                    "paths": [
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                    ],
                    "driver": (webdriver.Chrome, ChromeOptions, ChromeService)
                },
                "firefox": {
                    "paths": [
                        "/Applications/Firefox.app/Contents/MacOS/firefox"
                    ],
                    "driver": (webdriver.Firefox, FirefoxOptions, FirefoxService)
                }
            }
        else:  # Linux
            browsers = {
                "edge": {
                    "paths": [
                        "/usr/bin/microsoft-edge",
                        "/usr/bin/microsoft-edge-stable"
                    ],
                    "driver": (webdriver.Edge, EdgeOptions, EdgeService)
                },
                "chrome": {
                    "paths": [
                        "/usr/bin/google-chrome",
                        "/usr/bin/google-chrome-stable"
                    ],
                    "driver": (webdriver.Chrome, ChromeOptions, ChromeService)
                },
                "firefox": {
                    "paths": [
                        "/usr/bin/firefox"
                    ],
                    "driver": (webdriver.Firefox, FirefoxOptions, FirefoxService)
                }
            }

        # 检查每个浏览器是否可用
        for browser_name, browser_info in browsers.items():
            for path in browser_info["paths"]:
                if os.path.exists(path):
                    driver_class, options_class, service_class = browser_info["driver"]
                    return driver_class, options_class, service_class, path
                    
        return None

    def get_page_content(self, url, wait_time=5, max_retries=3):
        """
        使用给定的WebDriver打开并获取网页内容
        
        参数:
            url: 要访问的网页URL
            wait_time: 等待页面加载的时间（秒）
            max_retries: 最大重试次数
            
        返回:
            str: 网页内容
        """
        if not self.driver:
            return None

        for attempt in range(max_retries):
            try:
                # 访问URL
                self.driver.get(url)
                
                # 先等待一小段时间让页面开始加载
                time.sleep(1)
                
                # 等待页面加载完成
                wait = WebDriverWait(self.driver, wait_time)
                wait.until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )

                # 等待body元素出现并稳定
                body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # 再等待一小段时间确保动态内容加载完成
                time.sleep(1)
                
                # 获取页面内容
                page_content = self.driver.page_source
                if page_content and len(page_content.strip()) > 0:
                    return page_content
                    
            except Exception as e:
                print(f"第 {attempt + 1} 次尝试获取页面内容时发生错误: {str(e)}")
                if attempt == max_retries - 1:  # 如果是最后一次尝试
                    print("已达到最大重试次数，获取页面内容失败")
                    return None
                time.sleep(2)  # 在重试之前等待一段时间
                
        return None
        
    def create_webdriver(self):
        """
        创建并返回一个可用的WebDriver实例
        
        返回:
            WebDriver实例 或 None（如果没有可用的浏览器）
        """
        browser_info = self.check_browser_availability()
        if browser_info is None:
            print("未找到可用的浏览器")
            return None
            
        driver_class, options_class, service_class, browser_path = browser_info
        
        try:
            # 创建WebDriver选项
            options = options_class()
            options.add_argument('--headless')  # 无头模式
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # 创建WebDriver实例
            driver = driver_class(options=options)
            return driver
            
        except WebDriverException as e:
            print(f"创建WebDriver时发生错误: {str(e)}")
            return None

    def close_webdriver(self):
        """ 
        安全地关闭WebDriver实例
        """
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            print(f"关闭WebDriver时发生错误: {str(e)}")
