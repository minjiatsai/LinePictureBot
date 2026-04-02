import os
import random
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageSendMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# --- 請再次確認這裡的大小寫是否與 GitHub 完全一致 ---
GITHUB_USER = "minjiatsai"
GITHUB_REPO = "LinePictureBot"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/"
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
        photo_pool = []
        
        # 嘗試 1：自動從 GitHub API 抓取
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                files = response.json()
                photo_pool = [f['name'] for f in files if f['name'].lower().endswith(('.jpeg', '.jpg', '.png'))]
                print("成功從 API 取得照片清單")
        except Exception as e:
            print(f"API 抓取出錯: {e}")

        # 嘗試 2：如果 API 失敗 (photo_pool 是空的)，改用手動清單 (備援機制)
        if not photo_pool:
            print("切換至手動備援清單")
            # 這裡填入你目前確定的幾張檔名，確保 API 壞掉時也能抽
            photo_pool = ["IMG_6267.jpeg", "IMG_6268.jpeg", "IMG_6269.jpeg"]

        try:
            picked = random.choice(photo_pool)
            raw_github_url = BASE_URL + picked
            
            # 使用縮圖代理解決破圖問題
            compressed_url = f"https://images.weserv.nl/?url={raw_github_url}&w=800&q=60&output=jpg"
            
            image_message = ImageSendMessage(
                original_content_url=compressed_url,
                preview_image_url=compressed_url
            )
            line_bot_api.reply_message(event.reply_token, image_message)
            
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="目前無法抽獎，請稍後再試。"))

if __name__ == "__main__":
    app.run()
