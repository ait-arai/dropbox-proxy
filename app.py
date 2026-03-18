import os
from flask import Flask, request, render_template_string
import dropbox
from dropbox.exceptions import AuthError, ApiError
from dropbox.files import WriteMode

app = Flask(__name__)

# 環境変数
DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')

def get_dropbox_client():
    return dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

def get_folder_list():
    """Dropbox内のフォルダ一覧を取得。エラー時は詳細を画面に返す"""
    folders = [("/", "ルート直下")]
    try:
        dbx = get_dropbox_client()
        # ルート(空文字)から探索。recursiveを一旦Falseにして確実に取得を試みる
        res = dbx.files_list_folder('', recursive=False)
        
        for entry in res.entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                folders.append((entry.path_display, entry.path_display))
        
        # フォルダ名でソート
        return sorted(folders, key=lambda x: x[0])
    
    except AuthError:
        return [("/", "ルート直下 (エラー: 認証失敗/トークン無効)")]
    except ApiError as e:
        return [("/", f"ルート直下 (エラー: API制限/パス不正 {e})")]
    except Exception as e:
        # その他の予期せぬエラー
        return [("/", f"ルート直下 (取得失敗: {type(e).__name__})")]

# HTMLテンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dropbox Pro Upload</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; padding-top: 50px; background-color: #f0f4f8; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 450px; }
        h2 { color: #0061ff; margin-bottom: 20px; }
        label { font-weight: bold; display: block; margin-top: 15px; }
        select, input[type="file"] { width: 100%; margin: 8px 0 20px 0; padding: 12px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 14px; background-color: #0061ff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; }
        button:hover { background-color: #0050d5; }
        .info { font-size: 12px; color: #666; margin-bottom: 5px; }
    </style>
    <script>
        function confirmUpload() {
            return confirm("【確認】同名のファイルがある場合は「上書き」されます。続行しますか？");
        }
    </script>
</head>
<body>
    <div class="card">
        <h2>Dropbox アップロード</h2>
        <form action="/upload" method="post" enctype="multipart/form-data" onsubmit="return confirmUpload()">
            <label>1. ファイルを選択</label>
            <input type="file" name="file" required>
            
            <label>2. 保存先フォルダを選択</label>
            <div class="info">※Dropbox内のフォルダを自動取得しています</div>
            <select name="folder_path">
                {% for path, name in folders %}
                <option value="{{ path }}">{{ name }}</option>
                {% endfor %}
            </select>
            
            <button type="submit">アップロード実行</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    folders = get_folder_list()
    return render_template_string(HTML_TEMPLATE, folders=folders)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files: return "No file", 400
    file = request.files['file']
    folder_path = request.form.get('folder_path', '/')
    if file.filename == '': return "No filename", 400

    # パス結合（ルート直下対応）
    dropbox_path = f"/{file.filename}" if folder_path == "/" else f"{folder_path}/{file.filename}"

    try:
        dbx = get_dropbox_client()
        dbx.files_upload(
            file.read(), 
            dropbox_path, 
            mode=WriteMode('overwrite'), 
            autorename=False, 
            mute=True
        )
        return f"""
        <div style="text-align:center; padding-top:100px; font-family:sans-serif;">
            <h1 style="color:#2d8a3c;">アップロード完了（上書き成功）</h1>
            <p>保存先: {dropbox_path}</p>
            <a href="/">戻る</a>
        </div>
        """
    except Exception as e:
        return f"Error during upload: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
