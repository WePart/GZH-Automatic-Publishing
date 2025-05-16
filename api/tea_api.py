import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementNotInteractableException
import os
import shutil
import random

# 官方文档地址
# https://doc2.bitbrowser.cn/jiekou/ben-di-fu-wu-zhi-nan.html

# 此demo仅作为参考使用，以下使用的指纹参数仅是部分参数，完整参数请参考文档

url = "http://127.0.0.1:54345"
headers = {'Content-Type': 'application/json'}

def updateBrowser():  # 更新窗口，支持批量更新和按需更新，ids 传入数组，单独更新只传一个id即可，只传入需要修改的字段即可，比如修改备注，具体字段请参考文档，browserFingerPrint指纹对象不修改，则无需传入
    json_data = {'ids': ['93672cf112a044f08b653cab691216f0'],
                 'remark': '我是一个备注', 'browserFingerPrint': {}}
    res = requests.post(f"{url}/browser/update/partial",
                        data=json.dumps(json_data), headers=headers).json()
    print(res)


def openBrowser(id):  # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
    json_data = {"id": f'{id}'}
    res = requests.post(f"{url}/browser/open",
                        data=json.dumps(json_data), headers=headers).json()
    return res


def closeBrowser(id):  # 关闭窗口
    json_data = {'id': f'{id}'}
    requests.post(f"{url}/browser/close",
                  data=json.dumps(json_data), headers=headers).json()


def deleteBrowser(id):  # 删除窗口
    json_data = {'id': f'{id}'}
    print(requests.post(f"{url}/browser/delete",
          data=json.dumps(json_data), headers=headers).json())


class WeixinPublisher:
    def __init__(self, folder_name, author_name, browser_id=None, generate_cover=False):
        self.generate_cover = generate_cover
        if browser_id is None:
            print("必须提供 browser_id 参数")
            return None
            
        self.WZ_ZUOZHE = author_name
        self.BASE_PATH = r'E:\BaiduSyncdisk\自动化程序\文件库'
        self.AUTHOR_FOLDER = os.path.join(self.BASE_PATH, folder_name)
        self.PUBLISHED_FOLDER = os.path.join(self.AUTHOR_FOLDER, '已发布')
        self.browser_id = browser_id
        self.initialized = False
        
        # 检查文件夹和文件
        if not self.setup_folders():
            return None
            
        self.txt_files = self.check_available_files()
        if not self.txt_files:
            print(f"{self.AUTHOR_FOLDER} 中没有可发布的txt文件")
            return None
            
        # 只有在有文件可发布时才初始化浏览器
        if self.setup_driver():
            self.initialized = True
        
    def check_available_files(self):
        """检查是否有可用的txt文件"""
        if not os.path.exists(self.AUTHOR_FOLDER):
            print(f"作者文件夹不存在: {self.AUTHOR_FOLDER}")
            return []
        return [f for f in os.listdir(self.AUTHOR_FOLDER) if f.endswith('.txt')]

    def setup_folders(self):
        """设置必要的文件夹"""
        try:
            if not os.path.exists(self.PUBLISHED_FOLDER):
                os.makedirs(self.PUBLISHED_FOLDER)
                print(f"已创建发布文件夹: {self.PUBLISHED_FOLDER}")
            return True
        except Exception as e:
            print(f"创建文件夹时出错: {str(e)}")
            return False
            
    def setup_driver(self):
        """初始化浏览器驱动"""
        try:
            res = openBrowser(self.browser_id)
            print(res)
            
            driverPath = res['data']['driver']
            debuggerAddress = res['data']['http']
            
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)
            
            chrome_service = Service(driverPath)
            self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            
            # 等待浏览器完全加载
            time.sleep(3)
            
            # 检查是否已存在排版页面
            found_formatting_page = False
            current_handles = self.driver.window_handles
            
            for handle in current_handles:
                try:
                    self.driver.switch_to.window(handle)
                    time.sleep(1)  # 给页面切换一些时间
                    current_url = self.driver.current_url
                    
                    if 'doocs.github.io/md' in current_url:
                        found_formatting_page = True
                        # 确保页面已完全加载
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'CodeMirror'))
                        )
                        print("成功切换到已存在的排版页面")
                        break
                except Exception as e:
                    print(f"检查标签页时出错: {str(e)}")
                    continue
            
            # 如果没有找到排版页面，则新建一个
            if not found_formatting_page:
                print("未找到排版页面，创建新的排版页面")
                self.driver.execute_script("window.open('https://doocs.github.io/md/', '_blank');")
                time.sleep(2)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                # 等待新页面加载完成
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'CodeMirror'))
                )
            return True
        except Exception as e:
            print(f"初始化浏览器时出错: {str(e)}")
            return False

    def publish_articles(self, num_articles=5):
        """发布文章的主方法"""
        if not self.initialized:
            return False
            
        try:
            num_to_publish = min(num_articles, len(self.txt_files))
            if num_to_publish < num_articles:
                print(f"注意：只找到 {num_to_publish} 篇文章可发布，少于请求的 {num_articles} 篇")
            elif num_to_publish == 0:
                print("没有可发布的文章")
                return False
                
            published_count = 0
            for i in range(num_to_publish):
                try:
                    if self._publish_single_article(i):
                        published_count += 1
                except Exception as e:
                    print(f"发布第 {i+1} 篇文章时发生错误: {str(e)}")
                    continue

            print(f"发布任务完成！成功发布 {published_count} 篇文章")
            return True
        
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
            closeBrowser(self.browser_id)
            print("浏览器已关闭")
        except Exception as e:
            print(f"关闭浏览器时发生错误: {str(e)}")

    def _publish_single_article(self, index):
        """发布单篇文章"""
        try:
            txt_file = random.choice(self.txt_files)
            print(f"正在发布第 {index+1} 篇文章: {txt_file}")
            
            file_path = os.path.join(self.AUTHOR_FOLDER, txt_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 确保关闭 BitBrowser 首页并进行排版
            self.format_content(content)
            
            # 在开始发布前处理微信标签页
            self.handle_weixin_tabs()
            
            # 修改切换到微信公众号页面的逻辑
            if not self.switch_to_tab_with_url('mp.weixin.qq.com/cgi-bin/home'):
                # 如果没有找到微信主页，则新开一个
                self.driver.execute_script("window.open('https://mp.weixin.qq.com/', '_blank');")
                time.sleep(2)
                self.driver.switch_to.window(self.driver.window_handles[-1])
            else:
                # 如果找到已打开的微信页面，直接刷新
                self.driver.refresh()
                time.sleep(2)
            
            # 点击新建图文
            btn = self.driver.find_element(By.CLASS_NAME, 'new-creation__menu-content')
            btn.click()
            
            # 切换到新标签页
            time.sleep(2)
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[-1])
            
            # 输入标题
            title = os.path.splitext(txt_file)[0]
            biaoti = self.driver.find_element(By.CLASS_NAME, 'js_title')
            biaoti.send_keys(title)
            time.sleep(1)
            
            # 输入作者
            zuozhe = self.driver.find_element(By.CLASS_NAME, 'js_author')
            zuozhe.send_keys(self.WZ_ZUOZHE)
            time.sleep(1)
            
            # 输入正文（先尝试 iframe 方式，如果失败则尝试 div 方式）
            try:
                # 尝试 iframe 方式
                iframe = self.driver.find_element(By.ID, 'ueditor_0')
                self.driver.switch_to.frame(iframe)
                body = self.driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.CONTROL, 'v')
                self.driver.switch_to.default_content()
            except Exception as e:
                print("使用 iframe 方式失败，尝试 div 方式")
                # 尝试 div 方式
                editor_div = self.driver.find_element(By.XPATH, '//*[@id="ueditor_0"]/div/div/div/div')
                editor_div.send_keys(Keys.CONTROL, 'v')
            
            time.sleep(1)
            
            # 返回主文档
            self.driver.switch_to.default_content()
            time.sleep(1)
            
            # 原创声明
            element = self.driver.find_element(By.CLASS_NAME, 'js_unset_original_title')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            element.click()
            time.sleep(1)
            
            # 保存
            yc_baocun = self.driver.find_element(By.CLASS_NAME, 'weui-desktop-btn_primary')
            yc_baocun.click()
            time.sleep(2)
            
            # 发布
            baocun = self.driver.find_element(By.XPATH, '//*[@id="js_submit"]/button/span')
            baocun.click()
            time.sleep(2)
            
            # 关闭标签页
            self.driver.close()
            self.driver.switch_to.window(windows[0])
            time.sleep(3)
            
            # 发布成功后移动文件
            file_path = os.path.join(self.AUTHOR_FOLDER, txt_file)
            shutil.move(file_path, os.path.join(self.PUBLISHED_FOLDER, txt_file))
            print(f"文件 {txt_file} 已移动到已发布文件夹")
            self.txt_files.remove(txt_file)
            return True
            
        except Exception as e:
            print(f"发布文章 {txt_file} 时出错: {str(e)}")
            return False

    def switch_to_tab_with_url(self, url_pattern):
        current_handle = self.driver.current_window_handle
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if url_pattern in self.driver.current_url:
                return True
        self.driver.switch_to.window(current_handle)
        return False

    def wait_for_element(self, by, value, timeout=10, message=""):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            print(f"超时错误: {message}")
            return None
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return None

    def retry_on_error(self, func, max_attempts=3, delay=2):
        for attempt in range(max_attempts):
            try:
                result = func()
                return result
            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"最大重试次数已达到，操作失败: {str(e)}")
                    raise
                print(f"第 {attempt + 1} 次尝试失败，{delay} 秒后重试...")
                time.sleep(delay)

    def format_content(self, content):
        """使用 doocs.github.io/md 进行排版"""
        # 确保在正确的页面上操作
        if not self.switch_to_tab_with_url('doocs.github.io'):
            # 如果找不到排版页面，则新建一个
            self.driver.execute_script("window.open('https://doocs.github.io/md/', '_blank');")
            time.sleep(2)
            self.driver.switch_to.window(self.driver.window_handles[-1])
        
        # 等待编辑器加载完成
        if not self.wait_for_element(By.CLASS_NAME, 'CodeMirror', 
                                   message="排版页面编辑器加载超时"):
            raise Exception("排版页面加载失败")

        # 使用重试机制注入内容
        def inject_content():
            self.driver.execute_script("""
                var editor = document.querySelector('.CodeMirror').CodeMirror;
                editor.setValue(arguments[0]);
            """, content)
        self.retry_on_error(inject_content)

        time.sleep(1)
        # 等待并点击复制按钮
        copybtn = self.wait_for_element(By.XPATH, '//*[@id="app"]/div/header/div[2]/button[1]',
                                      message="复制按钮未找到")
        if copybtn:
            copybtn.click()
        else:
            raise Exception("无法找到复制按钮")

        time.sleep(2)
        return True

    def handle_weixin_tabs(self):
        """处理微信公众号标签页，只保留主页"""
        current_handles = self.driver.window_handles
        main_handle = None
        
        # 遍历所有标签页找到主页面
        for handle in current_handles:
            self.driver.switch_to.window(handle)
            if 'mp.weixin.qq.com/cgi-bin/home' in self.driver.current_url:
                main_handle = handle
                continue
            # 关闭非主页的微信相关标签页
            if 'mp.weixin.qq.com' in self.driver.current_url:
                self.driver.close()
        
        # 如果找到了主页面，切换到它
        if main_handle:
            self.driver.switch_to.window(main_handle)
            return True
        return False