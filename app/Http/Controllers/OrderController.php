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
use RuntimeException;

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
            Log::debug('Validation failed:', ['errors' => $validator->errors()->toArray()]);
            return redirect()
                ->back()
                ->withErrors($validator)
                ->withInput();
        }

        try {
            $file = $request->file('file');
            $yearMonth = $request->input('year_month');
            
            Log::debug('Starting file upload:', [
                'filename' => $file->getClientOriginalName(),
                'size' => $file->getSize(),
                'year_month' => $yearMonth,
                'content' => base64_encode($file->get())
            ]);
            
            DB::beginTransaction();
            
            Log::debug('Database state before parse:', [
                'connection' => DB::connection()->getDatabaseName(),
                'transaction_level' => DB::transactionLevel(),
                'orders_count' => Order::count()
            ]);
            
            $orders = $this->parser->parse(
                $file->get(),
                $file->getClientOriginalName()
            );
            
            Log::debug('Parsed orders:', [
                'count' => count($orders),
                'first_order' => $orders[0] ?? null,
                'all_orders' => $orders
            ]);
            
            Log::debug('Parsed orders:', [
                'count' => count($orders),
                'first_order' => $orders[0] ?? null
            ]);
            
            Log::debug('Parsed orders:', [
                'count' => count($orders),
                'first_order' => $orders[0] ?? null
            ]);

            if (empty($orders)) {
                throw new RuntimeException('ファイルの内容が正しくありません。');
            }

            Log::debug('Creating orders:', ['orders' => $orders]);
            foreach ($orders as $orderData) {
                if (empty($orderData['業者ID']) || empty($orderData['業者名'])) {
                    throw new RuntimeException('必須項目が不足しています。');
                }

                $order = Order::create([
                    'year_month' => $yearMonth,
                    'vendor_id' => $orderData['業者ID'],
                    'vendor_name' => $orderData['業者名'],
                    'building_name' => $orderData['建物名'],
                    'number' => $orderData['番号'],
                    'reception_details' => $orderData['受付内容'],
                    'payment_amount' => $orderData['支払金額'],
                    'completion_date' => $orderData['完工日'],
                    'payment_date' => $orderData['支払日'],
                    'billing_date' => $orderData['請求日'],
                    'erase_flg' => false
                ]);
                Log::debug('Created order:', ['order' => $order->toArray()]);
            }

            Log::debug('Before commit:', [
                'orders_count' => Order::count(),
                'transaction_level' => DB::transactionLevel()
            ]);
            
            DB::commit();
            
            Log::debug('After commit:', [
                'orders_count' => Order::count(),
                'transaction_level' => DB::transactionLevel()
            ]);
            
            $message = '発注書一覧が正常にアップロードされました。';

            if ($request->wantsJson()) {
                return response()->json(['message' => $message]);
            }

            return redirect()->route('orders.upload.form')
                ->with('success', $message);
        } catch (RuntimeException $e) {
            if (DB::transactionLevel() > 0) {
                DB::rollBack();
            }
            Log::error('Order parse error:', ['error' => $e->getMessage()]);
            return redirect()
                ->back()
                ->withErrors(['file' => $e->getMessage()])
                ->withInput();
        } catch (ValidationException $e) {
            if (DB::transactionLevel() > 0) {
                DB::rollBack();
            }
            Log::error('Validation error:', ['error' => $e->errors()]);
            return redirect()
                ->back()
                ->withErrors($e->errors())
                ->withInput();
        } catch (Exception $e) {
            if (DB::transactionLevel() > 0) {
                DB::rollBack();
            }
            Log::error('Order upload error:', ['error' => $e->getMessage()]);
            return redirect()
                ->back()
                ->withErrors(['file' => 'ファイルのアップロード中にエラーが発生しました。'])
                ->withInput();
        }
    }
}
