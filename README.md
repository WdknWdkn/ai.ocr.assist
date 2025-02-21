# AI OCR Assist

OCRアシスト機能を提供するWebアプリケーション

## 開発環境のセットアップ / Development Environment Setup

### 必要条件 / Requirements

- Docker
- Docker Compose
- Git

### セットアップ手順 / Setup Instructions

1. リポジトリのクローン / Clone the repository
```bash
git clone https://github.com/WdknWdkn/ai.ocr.assist.git
cd ai.ocr.assist
```

2. 環境設定ファイルの作成 / Create environment file
```bash
cp .env.example .env
```

3. Dockerコンテナの起動 / Start Docker containers
```bash
./vendor/bin/sail up -d
```

4. 依存パッケージのインストール / Install dependencies
```bash
./vendor/bin/sail composer install
./vendor/bin/sail npm install
```

5. アプリケーションキーの生成 / Generate application key
```bash
./vendor/bin/sail artisan key:generate
```

6. データベースのマイグレーション / Run database migrations
```bash
./vendor/bin/sail artisan migrate
```

7. フロントエンド開発サーバーの起動 / Start frontend development server
```bash
./vendor/bin/sail npm run dev
```

### アクセス方法 / Access Information

- メインアプリケーション / Main Application: http://localhost
- メール確認用UI / Mail Testing UI (Mailpit): http://localhost:8025

### 開発環境の特徴 / Development Environment Features

- Laravel Sail (Docker)による開発環境
- Laravel 10.x
- React + Inertia.js
- MySQL 8.0
- 日本時間対応 / Japanese timezone support
- ユーザー認証機能 / User authentication system

### テスト用アカウント / Test Account

```
Email: test@example.com
Password: password
```

### 便利なコマンド / Useful Commands

```bash
# コンテナの停止 / Stop containers
./vendor/bin/sail down

# コンポーザーパッケージのインストール / Install Composer packages
./vendor/bin/sail composer require package-name

# NPMパッケージのインストール / Install NPM packages
./vendor/bin/sail npm install package-name

# テストの実行 / Run tests
./vendor/bin/sail test

# アセットのビルド / Build assets
./vendor/bin/sail npm run build
```

## トラブルシューティング / Troubleshooting

1. ポートの競合 / Port conflicts
```bash
# 既存のプロセスを確認 / Check existing processes
sudo lsof -i :80
sudo lsof -i :3306

# 必要に応じてプロセスを停止 / Stop processes if needed
sudo kill -9 <PID>
```

2. パーミッションエラー / Permission errors
```bash
# ストレージディレクトリの権限修正 / Fix storage directory permissions
./vendor/bin/sail artisan storage:link
chmod -R 777 storage bootstrap/cache
```
