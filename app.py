import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 環境変数の取得
DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')

def get_access_token():
    """リフレッシュトークンを使用して新しいアクセストークンを取得"""
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET,
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

@app.route('/upload', methods=['POST'])
def upload_to_dropbox():
    # 1. wxOから送られてくる情報を取得
    # ファイル本体、ファイル名、保存先フォルダパス
    file = request.files.get('file')
    file_name = request.form.get('file_name')
    folder_path = request.form.get('folder_path', '') # 指定がなければルート

    if not file or not file_name:
        return jsonify({"error": "Missing file or file_name"}), 400

    # 2. Dropbox上のフルパスを生成（例: /MyFolder/test.pdf）
    # フォルダパスの先頭にスラッシュがない場合は補完
    full_path = f"/{folder_path.strip('/')}/{file_name}".replace('//', '/')

    access_token = get_access_token()
    
    # 3. Dropbox APIへ転送
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": f'{{"path": "{full_path}","mode": "add","autorename": true,"mute": false,"strict_conflict": false}}',
        "Content-Type": "application/octet-stream"
    }

    response = requests.post(url, headers=headers, data=file.read())

    if response.status_code == 200:
        return jsonify({"message": f"Successfully uploaded to {full_path}"}), 200
    else:
        return jsonify({"error": response.text}), response.status_code

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
