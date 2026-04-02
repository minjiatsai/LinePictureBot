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
    # 當用戶輸入「抽」的時候
    if event.message.text == "抽":
        try:
            # 1. 向 GitHub API 請求檔案清單
            response = requests.get(API_URL)
            if response.status_code != 200:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="暫時無法讀取相簿，請檢查網路。"))
                return
            
            files = response.json()
            
            # 2. 過濾出圖片檔案 (支援 jpeg, jpg, png, 並忽略大小寫)
            photo_pool = [
                f['name'] for f in files 
                if f['name'].lower().endswith(('.jpeg', '.jpg', '.png'))
            ]
            
            if not photo_pool:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="相簿裡目前沒有照片喔！"))
                return

            # 3. 隨機抽一張並組合完整網址
            picked = random.choice(photo_pool)
            img_url = BASE_URL + picked
            
            # 4. 回傳圖片訊息
            image_message = ImageSendMessage(
                original_content_url=img_url,
                preview_image_url=img_url
            )
            line_bot_api.reply_message(event.reply_token, image_message)

        except Exception as e:
            print(f"Error: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="系統忙碌中，請稍後再試。"))

if __name__ == "__main__":
    app.run()
