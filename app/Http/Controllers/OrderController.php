<?php

namespace App\Http\Controllers;

use App\Models\Order;
use App\Services\PythonOrderParser;
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
                foreach ($orders as $orderData) {
                    Log::debug('Processing order data:', [
                        'raw_data' => $orderData,
                        'keys' => array_keys($orderData)
                    ]);

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
                        'prepared_data' => $data,
                        'year_month' => $yearMonth,
                        'vendor_id' => (int)$orderData['業者ID']
                    ]);

                    $order = Order::create($data);
                    Log::debug('Created order:', [
                        'order_id' => $order->id,
                        'order_data' => $order->toArray()
                    ]);
                }

                DB::commit();

                return redirect()->route('orders.upload.form')
                    ->with('success', '発注書一覧が正常にアップロードされました。');
            } catch (Exception $e) {
                DB::rollBack();
                throw $e;
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
