<?php

namespace App\Http\Controllers;

use App\Services\PythonInvoiceParser;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Inertia\Inertia;

class InvoiceController extends Controller
{
    private PythonInvoiceParser $parser;

    public function __construct(PythonInvoiceParser $parser)
    {
        $this->parser = $parser;
    }

    public function showUploadForm()
    {
        return Inertia::render('Invoices/Upload');
    }

    public function upload(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'file' => 'required|file|mimes:pdf,jpg,jpeg,png|max:1024'
        ], [
            'file.required' => 'ファイルを選択してください。',
            'file.file' => '有効なファイルを選択してください。',
            'file.mimes' => 'PDF、JPG、またはPNG形式のファイルを選択してください。',
            'file.max' => 'ファイルサイズは1MB以下にしてください。'
        ]);

        if ($validator->fails()) {
            return redirect()->back()->withErrors($validator);
        }

        try {
            $file = $request->file('file');
            $content = $file->get();
            $data = $this->parser->parse($content, $file->getClientOriginalName());

            return redirect()->back()
                ->with('invoice_data', $data);
        } catch (\Exception $e) {
            return redirect()->back()->withErrors(['file' => $e->getMessage()]);
        }
    }
}
