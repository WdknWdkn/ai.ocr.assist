<?php

namespace App\Http\Controllers;

use App\Imports\OrdersImport;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;
use Maatwebsite\Excel\Facades\Excel;

class OrderController extends Controller
{
    public function showUploadForm(): Response
    {
        return Inertia::render('Orders/Upload');
    }
    public function upload(Request $request)
    {
        $request->validate([
            'file' => 'required|file|mimes:xlsx,csv|max:1024',
            'year_month' => 'required|string|regex:/^\d{4}-\d{2}$/' // YYYY-MM format
        ]);

        Excel::import(
            new OrdersImport($request->year_month),
            $request->file('file')
        );

        $message = '発注書一覧が正常にアップロードされました。';

        if ($request->wantsJson()) {
            return response()->json([
                'message' => $message
            ]);
        }

        return Inertia::render('Orders/Upload', [
            'flash' => [
                'success' => $message
            ]
        ]);
    }
}
