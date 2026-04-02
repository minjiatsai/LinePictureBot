import os
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageSendMessage

app = Flask(__name__)

# 從環境變數讀取，不要直接把 Secret 寫在程式碼裡，這樣比較安全
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 指向你的 GitHub 原始圖片路徑
BASE_URL = "https://raw.githubusercontent.com/minjiatsai/LinePictureBot/main/"

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
        # 請確認下方的檔名與你 GitHub 上的完全一致
        photo_pool = ["1.jpg", "2.jpg", "3.jpg"] 
        
        picked = random.choice(photo_pool)
        img_url = BASE_URL + picked
        
        # 建立圖片訊息 (LINE 要求原圖與預覽圖網址都要提供，我們用同一張即可)
        image_message = ImageSendMessage(
            original_content_url=img_url,
            preview_image_url=img_url
        )
        line_bot_api.reply_message(event.reply_token, image_message)

if __name__ == "__main__":
    app.run()
