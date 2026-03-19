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

import os
from flask import Flask, request, render_template_string
import dropbox
from dropbox.exceptions import AuthError, ApiError
from dropbox.files import WriteMode

app = Flask(__name__)

# 環境変数（Code Engineの「環境変数」タブで設定するもの）
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
    """Dropbox内の全フォルダを取得し、階層構造リストを作成する"""
    # 初期値としてルートを設定
    folders = [("/", "🏠 ルート直下", 0)]
    try:
        dbx = get_dropbox_client()
        # recursive=True で全階層をスキャン
        res = dbx.files_list_folder('', recursive=True)
        
        entries = []
        for entry in res.entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                # スラッシュの数で階層の深さを判定
                depth = entry.path_display.count('/')
                entries.append((entry.path_display, entry.name, depth))
        
        # パス順に並び替えて親子関係を維持
        entries.sort(key=lambda x: x[0])
        
        for path, name, depth in entries:
            # 視覚的な階層（インデント）を全角スペースで表現
            display_name = f"{'　' * (depth-1)} 📂 {name}"
            folders.append((path, display_name, depth))
            
        return folders
    except Exception as e:
        print(f"Folder List Error: {e}")
        # 取得失敗時はルートのみ表示（エラー内容を付記）
        return [("/", f"🏠 ルート直下 (取得失敗: {type(e).__name__})", 0)]

# HTMLテンプレート（エクスプローラー風UI ＋ 手入力）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dropbox Explorer Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: "Segoe UI", sans-serif; background-color: #f3f4f6; display: flex; justify-content: center; padding: 20px; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 100%; max-width: 500px; }
        h2 { color: #0061ff; font-size: 1.5rem; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        
        label { font-weight: bold; display: block; margin: 15px 0 8px; font-size: 14px; color: #4a5568; }
        input[type="file"] { width: 100%; padding: 12px; border: 2px dashed #cbd5e0; border-radius: 8px; cursor: pointer; background: #fff; box-sizing: border-box; }

        /* エクスプローラーエリア */
        .explorer-container { 
            border: 1px solid #e2e8f0; border-radius: 8px; max-height: 250px; overflow-y: auto; background: #fff; margin-bottom: 10px;
        }
        .folder-item { border-bottom: 1px solid #f7fafc; position: relative; }
        .folder-item input[type="radio"] { position: absolute; opacity: 0; width: 100%; height: 100%; cursor: pointer; z-index: 2; }
        .folder-label { display: block; padding: 10px 15px; font-size: 14px; white-space: nowrap; cursor: pointer; }
        
        /* ラジオボタンが選択された時のスタイル */
        .folder-item input[type="radio"]:checked + .folder-label { background-color: #0061ff; color: white; }
        .folder-item:hover .folder-label { background-color: #f0f7ff; }
        .folder-item input[type="radio"]:checked + .folder-label:hover { background-color: #0061ff; }

        /* 手入力用テキストボックス */
        .manual-path-input {
            width: 100%; padding: 12px; border: 1px solid #0061ff; border-radius: 8px; 
            font-size: 14px; font-family: monospace; box-sizing: border-box; background-color: #fff;
        }
        .info-text { font-size: 11px; color: #718096; margin-top: 5px; }

        button { 
            width: 100%; padding: 16px; background-color: #0061ff; color: white; border: none; 
            border-radius: 8px; cursor: pointer; font-size: 18px; font-weight: bold; margin-top: 20px;
            transition: background 0.2s;
        }
        button:hover { background-color: #0050d5; }
    </style>
    <script>
        // リストでフォルダを選んだら、テキストボックスにパスを自動反映
        function updateManualPath(path) {
            document.getElementById('manual_path').value = path;
        }
    </script>
</head>
<body>
    <div class="card">
        <h2>Dropbox アップロード</h2>
        <form action="/upload" method="post" enctype="multipart/form-data" onsubmit="return confirm('指定したパスに「上書き」保存します。よろしいですか？')">
            
            <label>1. ファイルを選択</label>
            <input type="file" name="file" required>
            
            <label>2. 保存先フォルダを選択 (エクスプローラー式)</label>
            <div class="explorer-container">
                {% for path, name, depth in folders %}
                <div class="folder-item">
                    <input type="radio" name="path_select" value="{{ path }}" onclick="updateManualPath('{{ path }}')" {% if loop.first %}checked{% endif %}>
                    <div class="folder-label">{{ name }}</div>
                </div>
                {% endfor %}
            </div>
            
            <label>3. 保存パス (直接編集可能)</label>
            <input type="text" name="folder_path" id="manual_path" class="manual-path-input" value="/">
            <div class="info-text">※上のリストで選択するか、新しいパスを直接入力してください。</div>
            
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
    if 'file' not in request.files: return "No file part", 400
    file = request.files['file']
    # リストの選択結果ではなく、自由入力が可能なテキストボックス(folder_path)の値を使用
    folder_path = request.form.get('folder_path', '/')
    if file.filename == '': return "No selected file", 400

    # 保存パスの成形
    folder_path = folder_path.rstrip('/')
    if not folder_path.startswith('/'):
        folder_path = '/' + folder_path
        
    dropbox_path = f"{folder_path}/{file.filename}" if folder_path != "" else f"/{file.filename}"
    # スラッシュの重複を防止
    if dropbox_path.startswith('//'): dropbox_path = dropbox_path[1:]

    try:
        dbx = get_dropbox_client()
        # ファイルのアップロード（上書きモード）
        dbx.files_upload(
            file.read(), 
            dropbox_path, 
            mode=WriteMode('overwrite'), 
            mute=True
        )
        return f"""
        <div style="text-align:center; padding-top:100px; font-family:sans-serif;">
            <h2 style="color:#2d8a3c;">アップロード完了</h2>
            <p>保存先: <strong>{dropbox_path}</strong></p>
            <hr style="width:50%; border:0; border-top:1px solid #eee; margin:20px auto;">
            <a href="/" style="color:#0061ff; text-decoration:none;">← 戻る</a>
        </div>
        """
    except Exception as e:
        return f"アップロード中にエラーが発生しました: {e}", 500

if __name__ == '__main__':
    # ポート番号は環境変数PORT（デフォルト8080）を使用
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
