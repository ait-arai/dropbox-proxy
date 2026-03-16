import os
import requests
from flask import Flask

app = Flask(__name__)

# Code Engineの環境変数（シークレット経由）から情報を取得
APP_KEY = os.environ.get('DROPBOX_APP_KEY')
APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')

def get_access_token():
    """リフレッシュトークンを使って新しいアクセストークンを取得する"""
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": APP_KEY,
        "client_secret": APP_SECRET,
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

@app.route('/')
def index():
    return "Dropbox Uploader is Running!"

@app.route('/upload_test')
def upload_test():
    try:
        access_token = get_access_token()
        if not access_token:
            return "Error: Could not get access token.", 500

        # Dropboxへアップロードするテストファイルの内容
        file_content = b"This is a test file uploaded from IBM Cloud Code Engine!"
        dropbox_path = "/test_from_ibm_cloud.txt"

        url = "https://content.dropboxapi.com/2/files/upload"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Dropbox-API-Arg": f'{{"path": "{dropbox_path}","mode": "overwrite"}}',
            "Content-Type": "application/octet-stream",
        }

        response = requests.post(url, headers=headers, data=file_content)
        
        if response.status_code == 200:
            return f"Success! File uploaded to Dropbox at {dropbox_path}"
        else:
            return f"Upload Failed: {response.text}", response.status_code

    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
