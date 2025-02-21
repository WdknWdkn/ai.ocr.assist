# AI OCR Assist

発注書一覧の管理とOCR処理を行うシステム

## 開発環境構築手順

### 必要条件
- Docker
- Docker Compose
- PHP 8.4
- Composer
- Node.js 18以上
- npm または yarn

### セットアップ手順

1. リポジトリのクローン
```bash
git clone https://github.com/WdknWdkn/ai.ocr.assist.git
cd ai.ocr.assist
```

2. 環境設定ファイルのコピー
```bash
cp .env.example .env
```

3. Composerパッケージのインストール
```bash
composer install
```

4. アプリケーションキーの生成
```bash
./vendor/bin/sail artisan key:generate
```

5. Dockerコンテナの起動
```bash
./vendor/bin/sail up -d
```

6. データベースのマイグレーション
```bash
./vendor/bin/sail artisan migrate
```

7. フロントエンドの依存関係のインストール
```bash
npm install
```

8. フロントエンドの開発サーバー起動
```bash
npm run dev
```

### 開発用URL
- アプリケーション: http://localhost
- バックエンドAPI: http://localhost:80

## API仕様

### 発注書一覧アップロード API

#### エンドポイント
`POST /api/orders/upload`

#### リクエストパラメータ
- `file`: 発注書一覧エクセルファイル（必須）
  - 形式: xlsx, csv
  - サイズ制限: 1MB以下
- `year_month`: 年月（必須）
  - 形式: YYYY-MM（例: 2025-02）

#### リクエストヘッダー
```
Content-Type: multipart/form-data
Accept: application/json
```

#### レスポンス
```json
{
    "message": "発注書一覧が正常にアップロードされました。"
}
```

#### エラーレスポンス
```json
{
    "message": "The given data was invalid.",
    "errors": {
        "file": ["ファイルは必須です。"],
        "year_month": ["年月は「YYYY-MM」形式で入力してください。"]
    }
}
```

### データベース設計

#### ordersテーブル
| カラム名 | 型 | 説明 |
|---------|------|------|
| id | bigint | 主キー |
| year_month | string | 年月 |
| vendor_id | integer | 業者ID |
| vendor_name | string | 業者名 |
| building_name | string | 建物名 |
| number | integer | 番号 |
| reception_details | string | 受付内容 |
| payment_amount | integer | 支払金額 |
| completion_date | date | 完工日 |
| payment_date | date | 支払日 |
| billing_date | date | 請求日 |
| erase_flg | boolean | 照合完了フラグ |
| created_at | timestamp | 登録日 |
| updated_at | timestamp | 更新日 |
