import os
from flask import Flask

app = Flask(__name__)

@app.get('/<folder_name>')
def hello(folder_name):
    # まずは疎通確認用。後でDropbox連携ロジックを追加します
    return f"Target Folder: {folder_name} - Connection OK!"

if __name__ == "__main__":
    # Code Engineはデフォルトで8080ポートを使用します
    app.run(host='0.0.0.0', port=8080)