import os
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageSendMessage, TextSendMessage

app = Flask(__name__)

# 從環境變數讀取密鑰 (請確認 Render 後台已設定這兩個變數)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# GitHub 相關設定
GITHUB_USER = "minjiatsai"
GITHUB_REPO = "LinePictureBot"
# 圖片原始檔案網址前綴
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/"

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
    if "抽" in event.message.text:
        try:
            # 1. 定義你的圖片數字範圍
            start_num = 6267
            end_num = 6295
            
            # 2. 自動生成所有檔名清單 (例如: IMG_6267.jpeg, IMG_6268.jpeg ...)
            photo_pool = [f"IMG_{i}.jpeg" for i in range(start_num, end_num + 1)]
            
            # 3. 隨機抽一張
            picked = random.choice(photo_pool)
            raw_github_url = BASE_URL + picked
            
            # 4. 使用 weserv 縮圖代理 (解決手機照片檔案太大導致破圖的問題)
            # 強制寬度 800px，品質 60%，輸出為 jpg
            compressed_url = f"https://images.weserv.nl/?url={raw_github_url}&w=800&q=60&output=jpg"
            
            # 5. 回傳圖片訊息
            image_message = ImageSendMessage(
                original_content_url=compressed_url,
                preview_image_url=compressed_url
            )
            line_bot_api.reply_message(event.reply_token, image_message)

        except Exception as e:
            print(f"Error: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="發生錯誤，請稍後再試。"))

if __name__ == "__main__":
    app.run()
