import requests
import os
import random
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
    text = event.message.text or ""
    
    try:
        if "侯爺" in text:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="這一聲侯爺，你是改不了是嗎？")
            )
            return

        if "抽" in text:
            # --- 修正後的邏輯：直接去 GitHub 抓清單 ---
            api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                files = response.json()
                # 只篩選出是檔案且副檔名是圖片的 (排除 .py, README 等)
                photo_pool = [f['name'] for f in files if f['type'] == 'file' and f['name'].lower().endswith(('.jpg', '.jpeg', '.png'))]
                
                if not photo_pool:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="圖庫空空如也..."))
                    return
                
                # 從「真的存在」的檔案清單裡抽
                picked = random.choice(photo_pool)
                raw_github_url = BASE_URL + picked
                
                # 這裡繼續用你原本的壓縮服務
                compressed_url = f"https://images.weserv.nl/?url={raw_github_url}&w=800&q=60&output=jpg"

                image_message = ImageSendMessage(
                    original_content_url=compressed_url,
                    preview_image_url=compressed_url
                )
                line_bot_api.reply_message(event.reply_token, image_message)
            else:
                # 如果 API 失敗（例如被限流），回報錯誤
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="暫時無法連接圖庫。"))
            return

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    app.run()
