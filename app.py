import os
import random
import requests  # 新增：用於串接 GitHub API
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageSendMessage, TextSendMessage

app = Flask(__name__)

# 從環境變數讀取密鑰
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# GitHub 相關設定
GITHUB_USER = "minjiatsai"
GITHUB_REPO = "LinePictureBot"
# 原始圖片下載網址前綴
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/"
# GitHub API 網址 (用於獲取檔案清單)
API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "抽":
        try:
            # 1. 自動向 GitHub API 請求檔案清單
            response = requests.get(API_URL)
            
            # 如果失敗，通常是因為私有專案沒權限或流量限制
            if response.status_code != 200:
                print(f"!!! GitHub API Error: {response.status_code}")
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="讀取相簿失敗，請確認 Repo 是否為公開。"))
                return
            
            files = response.json()
            
            # 2. 自動過濾出所有圖片 (不管檔名是什麼，只要是 .jpeg/.jpg/.png 都要)
            photo_pool = [
                f['name'] for f in files 
                if f['name'].lower().endswith(('.jpeg', '.jpg', '.png'))
            ]
            
            if not photo_pool:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="相簿裡沒照片喔！"))
                return

            # 3. 隨機抽一張
            picked = random.choice(photo_pool)
            raw_github_url = BASE_URL + picked
            
            # 4. 使用縮圖代理 (這行一定要留著，不然手機照片太大會破圖)
            compressed_url = f"https://images.weserv.nl/?url={raw_github_url}&w=800&q=60&output=jpg"
            
            image_message = ImageSendMessage(
                original_content_url=compressed_url,
                preview_image_url=compressed_url
            )
            line_bot_api.reply_message(event.reply_token, image_message)

        except Exception as e:
            print(f"Error: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="發生錯誤。"))

if __name__ == "__main__":
    app.run()
