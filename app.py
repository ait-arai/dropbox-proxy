import os
from flask import Flask, request, render_template_string, jsonify
import dropbox
from dropbox.exceptions import AuthError, ApiError
from dropbox.files import WriteMode  #

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
    folders = [("/", "🏠 ルート直下", 0)]
    try:
        dbx = get_dropbox_client()
        res = dbx.files_list_folder('', recursive=True)
        entries = []
        for entry in res.entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                depth = entry.path_display.count('/')
                entries.append((entry.path_display, entry.name, depth))
        entries.sort(key=lambda x: x[0])
        for path, name, depth in entries:
            display_name = f"{'　' * (depth-1)} 📂 {name}"
            folders.append((path, display_name, depth))
        return folders
    except:
        return [("/", "🏠 ルート直下", 0)]

@app.route('/check_file', methods=['POST'])
def check_file():
    data = request.json
    folder = data.get('folder', '/').rstrip('/')
    filename = data.get('filename', '')
    
    # パス結合の修正
    if folder == "":
        full_path = f"/{filename}"
    else:
        full_path = f"{folder}/{filename}"
    
    # 二重スラッシュ防止
    full_path = full_path.replace('//', '/')
    
    try:
        dbx = get_dropbox_client()
        dbx.files_get_metadata(full_path)
        return jsonify({"exists": True})
    except:
        return jsonify({"exists": False})

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
        input[type="file"] { width: 100%; padding: 12px; border: 2px dashed #cbd5e0; border-radius: 8px; box-sizing: border-box; }
        .explorer-container { border: 1px solid #e2e8f0; border-radius: 8px; max-height: 200px; overflow-y: auto; background: #fff; margin-bottom: 10px; }
        .folder-item { border-bottom: 1px solid #f7fafc; position: relative; }
        .folder-item input[type="radio"] { position: absolute; opacity: 0; width: 100%; height: 100%; cursor: pointer; z-index: 2; }
        .folder-label { display: block; padding: 10px 15px; font-size: 14px; white-space: nowrap; }
        .folder-item input[type="radio"]:checked + .folder-label { background-color: #0061ff; color: white; }
        .manual-path-input { width: 100%; padding: 12px; border: 1px solid #0061ff; border-radius: 8px; font-size: 14px; box-sizing: border-box; }
        button { width: 100%; padding: 16px; background-color: #0061ff; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 18px; font-weight: bold; margin-top: 20px; }
    </style>
    <script>
        function updateManualPath(path) {
            document.getElementById('manual_path').value = path;
        }

        async function handleUpload(event) {
            event.preventDefault();
            const form = event.target;
            const fileInput = form.file;
            const folderPath = document.getElementById('manual_path').value;
            
            if (!fileInput.files.length) return;
            const filename = fileInput.files[0].name;

            const response = await fetch('/check_file', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ folder: folderPath, filename: filename })
            });
            const result = await response.json();

            if (result.exists) {
                if (!confirm("同名のファイルが既に存在します。上書きしますか？")) {
                    return;
                }
            }
            form.submit();
        }
    </script>
</head>
<body>
    <div class="card">
        <h2>Dropbox アップロード</h2>
        <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data" onsubmit="handleUpload(event)">
            <label>1. ファイルを選択</label>
            <input type="file" name="file" required>
            
            <label>2. 保存先フォルダを選択</label>
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
    folder_path = request.form.get('folder_path', '/').rstrip('/')
    if file.filename == '': return "No selected file", 400

    # パス成形のロジックをより確実に
    clean_folder = folder_path if folder_path.startswith('/') else '/' + folder_path
    if clean_folder == "/":
        dropbox_path = f"/{file.filename}"
    else:
        dropbox_path = f"{clean_folder}/{file.filename}"
    
    # 最終的なパスから二重スラッシュを除去
    dropbox_path = dropbox_path.replace('//', '/')

    try:
        dbx = get_dropbox_client()
        # ★修正ポイント: WriteMode.overwrite を使用
        dbx.files_upload(
            file.read(), 
            dropbox_path, 
            mode=WriteMode.overwrite, 
            mute=True
        )
        return f'<div style="text-align:center;padding-top:100px;font-family:sans-serif;"><h2>成功！</h2><p>保存先: {dropbox_path}</p><a href="/">戻る</a></div>'
    except ApiError as e:
        return f"Dropbox API Error: {e}", 500
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
