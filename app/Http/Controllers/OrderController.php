<?php

namespace App\Http\Controllers;

use App\Models\Order;
use App\Services\PythonOrderParser;
use App\Services\OrderSearchService;
use Exception;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Validator;
use Illuminate\Validation\ValidationException;
use Inertia\Inertia;
use Inertia\Response;

class OrderController extends Controller
{
    private PythonOrderParser $parser;

    public function __construct(PythonOrderParser $parser)
    {
        $this->parser = $parser;
    }

    public function index(Request $request)
    {
        $searchService = new OrderSearchService();
        $query = Order::query();
        
        $query = $searchService->applyFilters($query, $request->only(['year_month', 'vendor_name']));
        
        $orders = $query->orderBy('created_at', 'desc')
            ->paginate(15)
            ->withQueryString();
            
        return Inertia::render('Orders/Index', [
            'orders' => $orders,
            'filters' => $request->only(['year_month', 'vendor_name'])
        ]);
    }

    public function showUploadForm(): Response
    {
        return Inertia::render('Orders/Upload');
    }

    public function upload(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'file' => 'required|file|mimes:xlsx,csv|max:1024',
            'year_month' => [
                'required',
                'string',
                'regex:/^\d{4}-(0[1-9]|1[0-2])$/'
            ]
        ], [
            'file.required' => 'ファイルを選択してください。',
            'file.file' => '有効なファイルを選択してください。',
            'file.mimes' => 'ExcelまたはCSVファイルを選択してください。',
            'file.max' => 'ファイルサイズは1MB以下にしてください。',
            'year_month.required' => '年月を入力してください。',
            'year_month.regex' => '年月の形式が正しくありません。YYYY-MM形式で入力してください。'
        ]);

        if ($validator->fails()) {
            return redirect()
                ->back()
                ->withErrors($validator)
                ->withInput();
        }

        try {
            $file = $request->file('file');
            $yearMonth = $request->input('year_month');

            Log::debug('Starting file upload process', [
                'file_name' => $file->getClientOriginalName(),
                'file_size' => $file->getSize(),
                'year_month' => $yearMonth,
                'mime_type' => $file->getMimeType(),
                'extension' => $file->getClientOriginalExtension()
            ]);

            $content = $file->get();
            Log::debug('File content:', [
                'content_length' => strlen($content),
                'content_preview' => substr($content, 0, 1000),
                'content_type' => $file->getClientMimeType()
            ]);

            Log::debug('Parsing file with PythonOrderParser');
            $orders = $this->parser->parse($content, $file->getClientOriginalName());
            Log::debug('Parsed orders:', [
                'count' => count($orders),
                'first_order' => $orders[0] ?? null,
                'all_orders' => $orders
            ]);

            DB::beginTransaction();

            try {
                $successCount = 0;
                $skippedCount = 0;
                $errors = [];

                foreach ($orders as $index => $orderData) {
                    try {
                        Log::debug('Processing order data:', [
                            'row' => $index + 1,
                            'raw_data' => $orderData,
                            'keys' => array_keys($orderData)
                        ]);

                        // データの検証
                        if (!isset($orderData['業者ID']) || !is_numeric($orderData['業者ID'])) {
                            $errors[] = ($index + 1) . "行目: 業者IDが不正です";
                            $skippedCount++;
                            continue;
                        }
                        if (!isset($orderData['業者名']) || empty(trim($orderData['業者名']))) {
                            $errors[] = ($index + 1) . "行目: 業者名が未入力です";
                            $skippedCount++;
                            continue;
                        }
                        if (!isset($orderData['建物名']) || empty(trim($orderData['建物名']))) {
                            $errors[] = ($index + 1) . "行目: 建物名が未入力です";
                            $skippedCount++;
                            continue;
                        }
                        if (!isset($orderData['番号']) || !is_numeric($orderData['番号'])) {
                            $errors[] = ($index + 1) . "行目: 番号が不正です";
                            $skippedCount++;
                            continue;
                        }
                        if (!isset($orderData['受付内容']) || empty(trim($orderData['受付内容']))) {
                            $errors[] = ($index + 1) . "行目: 受付内容が未入力です";
                            $skippedCount++;
                            continue;
                        }
                        if (!isset($orderData['支払金額']) || !is_numeric($orderData['支払金額'])) {
                            $errors[] = ($index + 1) . "行目: 支払金額が不正です";
                            $skippedCount++;
                            continue;
                        }

                        // 日付フィールドの検証
                        foreach (['完工日', '支払日', '請求日'] as $dateField) {
                            if (!isset($orderData[$dateField]) || empty(trim($orderData[$dateField]))) {
                                $errors[] = ($index + 1) . "行目: {$dateField}が未入力です";
                                $skippedCount++;
                                continue 2;
                            }
                            try {
                                $date = date('Y-m-d', strtotime($orderData[$dateField]));
                                if ($date === false) {
                                    $errors[] = ($index + 1) . "行目: {$dateField}の形式が不正です";
                                    $skippedCount++;
                                    continue 2;
                                }
                            } catch (Exception $e) {
                                $errors[] = ($index + 1) . "行目: {$dateField}の形式が不正です";
                                $skippedCount++;
                                continue 2;
                            }
                        }

                        $data = [
                            'year_month' => $yearMonth,
                            'vendor_id' => (int)$orderData['業者ID'],
                            'vendor_name' => $orderData['業者名'],
                            'building_name' => $orderData['建物名'],
                            'number' => (int)$orderData['番号'],
                            'reception_details' => $orderData['受付内容'],
                            'payment_amount' => (int)$orderData['支払金額'],
                            'completion_date' => date('Y-m-d', strtotime($orderData['完工日'])),
                            'payment_date' => date('Y-m-d', strtotime($orderData['支払日'])),
                            'billing_date' => date('Y-m-d', strtotime($orderData['請求日'])),
                            'erase_flg' => false
                        ];

                        Log::debug('Creating order:', [
                            'row' => $index + 1,
                            'prepared_data' => $data
                        ]);

                        $order = Order::create($data);
                        Log::debug('Created order:', [
                            'row' => $index + 1,
                            'order_id' => $order->id,
                            'order_data' => $order->toArray()
                        ]);

                        $successCount++;
                    } catch (Exception $e) {
                        Log::warning('Row processing failed:', [
                            'row' => $index + 1,
                            'error' => $e->getMessage(),
                            'data' => $orderData
                        ]);
                        $errors[] = ($index + 1) . "行目: " . $e->getMessage();
                        $skippedCount++;
                        continue;
                    }
                }

                DB::commit();

                $message = "{$successCount}件のデータを取り込みました。";
                if ($skippedCount > 0) {
                    $message .= " {$skippedCount}件のデータをスキップしました。";
                }

                return redirect()->route('orders.upload.form')
                    ->with('success', $message)
                    ->with('warnings', $errors);
            } catch (Exception $e) {
                DB::rollBack();
                Log::error('Transaction failed:', [
                    'error' => $e->getMessage(),
                    'trace' => $e->getTraceAsString()
                ]);
                return redirect()
                    ->back()
                    ->withErrors(['file' => 'データの保存中にエラーが発生しました。'])
                    ->withInput();
            }
        } catch (Exception $e) {
            Log::error('Upload failed:', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
                'file' => $request->file('file') ? [
                    'name' => $request->file('file')->getClientOriginalName(),
                    'size' => $request->file('file')->getSize(),
                    'mime' => $request->file('file')->getMimeType()
                ] : null,
                'year_month' => $request->input('year_month')
            ]);

            return redirect()
                ->back()
                ->withErrors(['file' => 'ファイルのアップロード中にエラーが発生しました。'])
                ->withInput();
        }
    }
}
