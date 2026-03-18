import os
from flask import Flask, request, render_template_string
import dropbox
from dropbox.exceptions import AuthError

app = Flask(__name__)

# 環境変数から情報を取得
DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')

# HTMLテンプレート（app.pyの中に直接書き込みます）
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dropbox アップロード</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; padding-top: 50px; background-color: #f5f7f9; }
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 400px; }
        h2 { color: #0061ff; }
        input[type="text"], input[type="file"] { width: 100%; margin: 10px 0 20px 0; padding: 10px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background-color: #0061ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #0050d5; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Dropbox アップロード</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <label>1. PC内のファイルを選択</label>
            <input type="file" name="file" required>
            <label>2. Dropbox保存先フォルダ (例: /Photos)</label>
            <input type="text" name="folder_name" placeholder="ルートに保存する場合は空欄か / ">
            <button type="submit">アップロード実行</button>
        </form>
    </div>
</body>
</html>
"""

SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>アップロード完了</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding-top: 100px; }
        .success { color: #2d8a3c; }
    </style>
</head>
<body>
    <h1 class="success">アップロード完了</h1>
    <p>ファイル: {{ filename }}</p>
    <p>保存先: {{ folder }}</p>
    <br>
    <a href="/">← 戻る</a>
</body>
</html>
"""

def get_dropbox_client():
    """リフレッシュトークンを使用してクライアントを生成"""
    return dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "ファイルがありません", 400
    
    file = request.files['file']
    folder_name = request.form.get('folder_name', '').strip()

    if file.filename == '':
        return "ファイル名が空です", 400

    # --- ルート直下対応のパス整形 ---
    clean_folder = folder_name.strip("/")
    if clean_folder == "":
        dropbox_path = f"/{file.filename}"
    else:
        dropbox_path = f"/{clean_folder}/{file.filename}"
    # ----------------------------

    try:
        dbx = get_dropbox_client()
        dbx.files_upload(file.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        return render_template_string(SUCCESS_HTML, filename=file.filename, folder=dropbox_path)
    
    except AuthError as e:
        return f"認証エラー: {e}", 401
    except Exception as e:
        return f"エラー: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
