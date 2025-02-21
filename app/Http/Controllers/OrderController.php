<?php

namespace App\Http\Controllers;

use App\Imports\OrdersImport;
use Illuminate\Http\Request;
use Maatwebsite\Excel\Facades\Excel;

class OrderController extends Controller
{
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

        return response()->json([
            'message' => 'Orders imported successfully'
        ]);
    }
}
