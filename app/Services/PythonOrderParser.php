<?php

namespace App\Services;

use Illuminate\Support\Facades\Process;
use Illuminate\Support\Facades\Log;
use RuntimeException;

class PythonOrderParser
{
    private const TIMEOUT_SECONDS = 30;
    private const TEMP_PREFIX = 'order_upload_';

    /**
     * Create a temporary file with the given content
     */
    private function createTempFile(string $content): string
    {
        $tempFile = tempnam(sys_get_temp_dir(), self::TEMP_PREFIX);
        if ($tempFile === false) {
            throw new RuntimeException('一時ファイルの作成に失敗しました。');
        }
        
        if (file_put_contents($tempFile, $content) === false) {
            unlink($tempFile);
            throw new RuntimeException('一時ファイルの書き込みに失敗しました。');
        }
        
        return $tempFile;
    }

    /**
     * Parse order file content using Python script
     */
    public function parse(string $content, string $filename): array
    {
        $tempFile = null;
        
        try {
            Log::debug('Starting Python parser:', [
                'filename' => $filename,
                'content_length' => strlen($content)
            ]);

            $tempFile = $this->createTempFile($content);
            Log::debug('Created temporary file:', [
                'temp_file' => $tempFile
            ]);

            $pythonScript = base_path('python-service/parse_order_lambda.py');
            Log::debug('Running Python script:', [
                'script_path' => $pythonScript,
                'script_exists' => file_exists($pythonScript),
                'script_permissions' => fileperms($pythonScript),
                'script_content' => file_exists($pythonScript) ? file_get_contents($pythonScript) : null,
                'content_preview' => substr($content, 0, 1000),
                'content_length' => strlen($content),
                'temp_file_exists' => file_exists($tempFile),
                'temp_file_content' => file_exists($tempFile) ? file_get_contents($tempFile) : null,
                'temp_file_permissions' => file_exists($tempFile) ? fileperms($tempFile) : null,
                'python_version' => shell_exec('python3 --version'),
                'working_directory' => getcwd()
            ]);
            
            Log::debug('Running Python script with args:', [
                'script' => $pythonScript,
                'temp_file' => $tempFile,
                'filename' => $filename,
                'script_exists' => file_exists($pythonScript),
                'temp_file_exists' => file_exists($tempFile),
                'temp_file_content' => file_exists($tempFile) ? file_get_contents($tempFile) : null,
                'working_dir' => getcwd()
            ]);

            $pythonVenv = dirname($pythonScript) . '/venv/bin/python';
            Log::debug('Using Python from venv:', ['python_path' => $pythonVenv]);

            $result = Process::timeout(self::TIMEOUT_SECONDS)->run([
                $pythonVenv,
                $pythonScript,
                $tempFile,
                $filename
            ], function ($type, $buffer) {
                Log::debug('Python output: ' . $buffer);
            });

            if ($result->failed()) {
                Log::error('Python execution failed:', [
                    'error' => $result->errorOutput()
                ]);
                throw new RuntimeException('ファイルの解析中にエラーが発生しました。');
            }

            $rawOutput = $result->output();
            $errorOutput = $result->errorOutput();
            
            Log::debug('Python script execution:', [
                'command' => 'python3 ' . $pythonScript . ' ' . $tempFile . ' ' . $filename,
                'raw_output' => $rawOutput,
                'error_output' => $errorOutput,
                'exit_code' => $result->exitCode(),
                'temp_file_exists' => file_exists($tempFile),
                'temp_file_size' => file_exists($tempFile) ? filesize($tempFile) : null,
                'temp_file_content' => file_exists($tempFile) ? file_get_contents($tempFile) : null
            ]);

            Log::debug('Raw Python output:', [
                'output' => $rawOutput,
                'error' => $result->errorOutput()
            ]);

            $output = json_decode($rawOutput, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                Log::error('JSON decode error:', [
                    'error' => json_last_error_msg(),
                    'raw_output' => $rawOutput
                ]);
                throw new RuntimeException('不正な出力形式です。');
            }

            Log::debug('Decoded Python output:', [
                'output' => $output
            ]);

            if (!$output || !is_array($output)) {
                Log::error('Invalid output format:', [
                    'output' => $output
                ]);
                throw new RuntimeException('不正な出力形式です。');
            }

            $orders = $output;
            Log::debug('Parsed orders:', [
                'orders' => $orders,
                'first_order' => $orders[0] ?? null,
                'count' => count($orders)
            ]);

            return $orders;
        } catch (ProcessTimedOutException $e) {
            Log::error('Python process timeout:', [
                'error' => $e->getMessage()
            ]);
            throw new RuntimeException('ファイルの処理がタイムアウトしました。');
        } catch (RuntimeException $e) {
            throw $e;
        } catch (Exception $e) {
            Log::error('Unexpected error:', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            throw new RuntimeException('ファイルの解析中にエラーが発生しました。');
        } finally {
            if ($tempFile !== null && file_exists($tempFile)) {
                unlink($tempFile);
                Log::debug('Cleaned up temporary file:', [
                    'temp_file' => $tempFile
                ]);
            }
        }
    }
}
