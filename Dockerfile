# 1. 軽量なPythonイメージを使用
FROM python:3.11-slim

# 2. コンテナ内の作業ディレクトリ
WORKDIR /app

# 3. 依存ライブラリのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. プログラム本体をコピー
COPY app.py .

# 5. アプリの起動（Port 8080）
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]