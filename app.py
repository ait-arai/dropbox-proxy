import os
import base64
from flask import Flask, request, jsonify
import dropbox

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    if not data:
        return jsonify({"message": "No input data"}), 400
        
    file_base64 = data.get('file_base64')
    file_name = data.get('file_name')
    folder_path = data.get('folder_path', '/')

    if not file_base64 or not file_name:
        return jsonify({"message": "Missing file data or name"}), 400

    try:
        file_content = base64.b64decode(file_base64)
        dbx = dropbox.Dropbox(os.environ.get('DROPBOX_ACCESS_TOKEN'))
        target_path = f"{folder_path}/{file_name}".replace('//', '/')
        
        dbx.files_upload(file_content, target_path, mode=dropbox.files.WriteMode.overwrite)
        return jsonify({"message": f"Successfully uploaded {file_name} to {folder_path}"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
