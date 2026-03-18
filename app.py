import os
from flask import Flask, request, render_template_string
import dropbox
from dropbox.files import WriteMode

app = Flask(__name__)

# 環境変数から認証情報を取得
APP_KEY = os.environ.get('DROPBOX_APP_KEY')
APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')

# ファイル選択用のHTML画面
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dropbox Direct Upload</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f7f9fb; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h2 { color: #0061ff; margin-top: 0; font-size: 1.5rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: bold; font-size: 0.9rem; }
        input[type="file"], input[type="text"] { width: 100%; padding: 10px; margin-bottom: 1.5rem; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #0061ff; color: white; border: none; padding: 12px; width: 100%; border-radius: 4px; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #0050d1; }
        .footer { margin-top: 1rem; font-size: 0.8rem; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Dropbox アップロード</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <label>1. PC内のファイルを選択</label>
            <input type="file" name="target_file" required>
            
            <label>2. Dropbox保存先フォルダ</label>
            <input type="text" name="folder_path" value="/" placeholder="例: /Photos">
            
            <button type="submit">アップロード実行</button>
        </form>
        <div class="footer">Code Engine Direct Transfer</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # ブラウザアクセス時にアップロード画面を表示
    return render_template_string(HTML_PAGE)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # 1. フォームデータの取得
        file = request.files.get('target_file')
        folder_path = request.form.get('folder_path', '/')

        if not file:
            return "ファイルが選択されていません。", 400

        # 2. Dropboxクライアントの初期化（リフレッシュトークン方式）
        # これにより、アクセストークンの期限切れを回避します
        dbx = dropbox.Dropbox(
            oauth2_refresh_token=REFRESH_TOKEN,
            app_key=APP_KEY,
            app_secret=APP_SECRET
        )

        # 3. 保存パスの組み立て
        # フォルダパスの整形（先頭のスラッシュを確認）
        base_folder = folder_path if folder_path.startswith('/') else '/' + folder_path
        # 末尾のスラッシュを削除してからファイル名を結合
        save_path = os.path.join(base_folder.rstrip('/'), file.filename).replace('\\', '/')

        # 4. アップロード実行
        file_content = file.read()
        dbx.files_upload(
            file_content,
            save_path,
            mode=WriteMode('overwrite')
        )

        return f"""
        <div style="text-align:center; padding:50px; font-family:sans-serif;">
            <h2 style="color:#28a745;">アップロード完了</h2>
            <p>ファイル: <b>{file.filename}</b></p>
            <p>保存先: <b>{save_path}</b></p>
            <br>
            <a href="/" style="color:#0061ff; text-decoration:none;">← 戻る</a>
        </div>
        """

    except Exception as e:
        return f"""
        <div style="text-align:center; padding:50px; font-family:sans-serif;">
            <h2 style="color:#dc3545;">エラーが発生しました</h2>
            <p style="color:#666;">{str(e)}</p>
            <br>
            <a href="/" style="color:#0061ff; text-decoration:none;">戻る</a>
        </div>
        """, 500

if __name__ == '__main__':
    # Code Engine環境のポート8080で起動
    app.run(host='0.0.0.0', port=8080)
