<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Http\Client\ConnectionException;
use RuntimeException;
use Exception;

class PythonOrderParser
{
    private const TIMEOUT_SECONDS = 30;
    private const API_URL = 'http://python.ocr:8000/api/v1/orders/parse';

    public function parse(string $content, string $filename): array
    {
        try {
            Log::debug('Starting API request:', [
                'filename' => $filename,
                'content_length' => strlen($content),
                'api_url' => self::API_URL
            ]);

            $response = Http::timeout(self::TIMEOUT_SECONDS)
                ->attach('file', $content, $filename)
                ->post(self::API_URL);

            Log::debug('API response:', [
                'status' => $response->status(),
                'headers' => $response->headers(),
                'body_preview' => substr($response->body(), 0, 1000)
            ]);

            if ($response->failed()) {
                $error = $response->json('detail') ?? 'ファイルの解析中にエラーが発生しました。';
                Log::error('API request failed:', [
                    'status' => $response->status(),
                    'error' => $error
                ]);
                throw new RuntimeException($error);
            }

            $data = $response->json('data');
            if (!is_array($data)) {
                Log::error('Invalid response format:', [
                    'data' => $data
                ]);
                throw new RuntimeException('不正な出力形式です。');
            }

            return $data;
        } catch (ConnectionException $e) {
            Log::error('API connection failed:', [
                'error' => $e->getMessage()
            ]);
            throw new RuntimeException('Python APIサービスに接続できません。');
        } catch (RuntimeException $e) {
            throw $e;
        } catch (Exception $e) {
            Log::error('Unexpected error:', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            throw new RuntimeException('ファイルの解析中にエラーが発生しました。');
        }
    }
}
