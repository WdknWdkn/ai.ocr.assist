<?php

namespace App\Services;

use Illuminate\Support\Facades\Process;
use Illuminate\Support\Facades\Log;
use RuntimeException;

class PythonOrderParser
{
    public function parse(string $content, string $filename): array
    {
        try {
            Log::debug('Starting Python parser:', [
                'filename' => $filename,
                'content_length' => strlen($content)
            ]);

            $base64Content = base64_encode($content);
            Log::debug('Base64 encoded content:', [
                'length' => strlen($base64Content)
            ]);

            $pythonScript = '/var/www/html/python-service/parse_order_lambda.py';
            Log::debug('Running Python script:', [
                'script' => $pythonScript,
                'exists' => file_exists($pythonScript),
                'permissions' => fileperms($pythonScript)
            ]);
            
            $result = Process::timeout(30)->run([
                'python3',
                $pythonScript,
                $base64Content,
                $filename
            ], function ($type, $buffer) {
                Log::debug('Python output: ' . $buffer);
            });

            Log::debug('Python command output:', [
                'stdout' => $result->output(),
                'stderr' => $result->errorOutput()
            ]);

            if ($result->failed()) {
                Log::error('Python parser error:', ['error' => $result->errorOutput()]);
                throw new RuntimeException('ファイルの解析中にエラーが発生しました。');
            }

            Log::debug('Raw Python output:', [
                'stdout' => $result->output(),
                'stderr' => $result->errorOutput()
            ]);

            $output = json_decode($result->output(), true);
            Log::debug('Decoded Python output:', ['output' => $output]);
            
            if (!$output || !isset($output['statusCode']) || !isset($output['body'])) {
                Log::error('Invalid Python output format:', ['output' => $output]);
                throw new RuntimeException('不正な出力形式です。');
            }

            if ($output['statusCode'] !== 200) {
                $error = json_decode($output['body'], true);
                throw new RuntimeException($error['error'] ?? 'ファイルの解析中にエラーが発生しました。');
            }

            $body = json_decode($output['body'], true);
            Log::debug('Decoded body:', ['body' => $body]);

            if (!isset($body['parsed_orders'])) {
                Log::error('Missing parsed_orders in output:', ['body' => $body]);
                throw new RuntimeException('不正な出力形式です。');
            }

            $orders = $body['parsed_orders'];
            Log::debug('Final parsed orders:', ['orders' => $orders]);

            return $orders;
        } catch (ProcessTimedOutException $e) {
            Log::error('Python process timeout:', ['error' => $e->getMessage()]);
            throw new RuntimeException('ファイルの処理がタイムアウトしました。');
        } catch (RuntimeException $e) {
            throw $e;
        } catch (Exception $e) {
            Log::error('Unexpected error:', ['error' => $e->getMessage()]);
            throw new RuntimeException('ファイルの解析中にエラーが発生しました。');
        }
    }
}
