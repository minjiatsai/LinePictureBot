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
        # 1. 如果留言含有「侯爺」→ 回文字
        if "侯爺" in text:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="這一聲侯爺，你是改不了是嗎？")
            )
            return

        # 2. 如果留言含有「抽」→ 出圖
        if "抽" in text:
            start_num = 6267
            end_num = 6316

            photo_pool = [f"IMG_{i}.jpeg" for i in range(start_num, end_num + 1)]
            picked = random.choice(photo_pool)
            raw_github_url = BASE_URL + picked

            compressed_url = f"https://images.weserv.nl/?url={raw_github_url}&w=800&q=60&output=jpg"

            image_message = ImageSendMessage(
                original_content_url=compressed_url,
                preview_image_url=compressed_url
            )
            line_bot_api.reply_message(event.reply_token, image_message)
            return

    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="發生錯誤，請稍後再試。")
        )

if __name__ == "__main__":
    app.run()
