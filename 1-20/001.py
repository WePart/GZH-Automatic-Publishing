import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.tea_api import WeixinPublisher

if __name__ == "__main__":
    # 001是文件夹名，XX是作者名，id是指纹浏览器id
    publisher = WeixinPublisher("001", "XX", browser_id="ba8bfb432dbc4511136f4d9470af2662") 
    publisher.publish_articles(1)