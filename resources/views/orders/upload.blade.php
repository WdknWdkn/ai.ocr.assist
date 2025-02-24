<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>発注書一覧アップロード</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h2 class="text-center">発注書一覧アップロード</h2>
                    </div>
                    <div class="card-body">
                        @if(session('success'))
                            <div class="alert alert-success">
                                {{ session('success') }}
                            </div>
                        @endif

                        @if($errors->any())
                            <div class="alert alert-danger">
                                <ul class="mb-0">
                                    @foreach($errors->all() as $error)
                                        <li>{{ $error }}</li>
                                    @endforeach
                                </ul>
                            </div>
                        @endif

                        <form action="{{ route('orders.upload') }}" method="POST" enctype="multipart/form-data">
                            @csrf
                            <div class="mb-3">
                                <label for="year_month" class="form-label">年月 (YYYY-MM)</label>
                                <input type="text" 
                                       class="form-control" 
                                       id="year_month" 
                                       name="year_month" 
                                       pattern="\d{4}-\d{2}"
                                       placeholder="2025-02"
                                       required>
                            </div>
                            <div class="mb-3">
                                <label for="file" class="form-label">発注書一覧エクセル</label>
                                <input type="file" 
                                       class="form-control" 
                                       id="file" 
                                       name="file"
                                       accept=".xlsx,.csv"
                                       required>
                                <div class="form-text">
                                    ファイルサイズ上限: 1MB<br>
                                    対応形式: Excel (.xlsx), CSV (.csv)
                                </div>
                            </div>
                            <div class="text-center">
                                <button type="submit" class="btn btn-primary">アップロード</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
