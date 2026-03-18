import os
from flask import Flask, render_template, request, redirect, url_for
import dropbox
from dropbox.exceptions import AuthError

app = Flask(__name__)

# 環境変数から情報を取得
DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')

def get_dropbox_client():
    """リフレッシュトークンを使用して、有効なアクセスTokenを持つクライアントを生成"""
    dbx = dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )
    return dbx

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "ファイルがありません", 400
    
    file = request.files['file']
    folder_name = request.form.get('folder_name', '').strip()

    if file.filename == '':
        return "ファイル名が空です", 400

    # --- パス作成の修正（ルート直下対応） ---
    # フォルダ名の前後にあるスラッシュを削る
    clean_folder = folder_name.strip("/")
    
    if clean_folder == "":
        # フォルダ指定がない、または "/" のみの場合はルート直下
        dropbox_path = f"/{file.filename}"
    else:
        # フォルダ指定がある場合
        dropbox_path = f"/{clean_folder}/{file.filename}"
    # ---------------------------------------

    try:
        dbx = get_dropbox_client()
        # ファイルをアップロード（上書きモード）
        dbx.files_upload(file.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        
        return render_template('success.html', filename=file.filename, folder=dropbox_path)
    
    except AuthError as e:
        return f"認証エラーが発生しました。トークンを確認してください: {e}", 401
    except Exception as e:
        return f"エラーが発生しました: {e}", 500

if __name__ == '__main__':
    # Code Engineなどの環境に合わせてポート番号を動的に取得
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
