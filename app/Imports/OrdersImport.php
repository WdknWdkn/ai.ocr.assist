<?php

namespace App\Imports;

use App\Models\Order;
use Carbon\Carbon;
use Maatwebsite\Excel\Concerns\ToModel;
use Maatwebsite\Excel\Concerns\WithHeadingRow;
use Maatwebsite\Excel\Concerns\WithValidation;

class OrdersImport implements ToModel, WithHeadingRow, WithValidation
{
    private $year_month;

    public function __construct(string $year_month)
    {
        $this->year_month = $year_month;
    }

    public function model(array $row)
    {
        return new Order([
            'year_month' => $this->year_month,
            'vendor_id' => $row['業者id'],
            'vendor_name' => $row['業者名'],
            'building_name' => $row['建物名'],
            'number' => $row['番号'],
            'reception_details' => $row['受付内容'],
            'payment_amount' => $row['支払金額'],
            'completion_date' => $this->parseDate($row['完工日']),
            'payment_date' => $this->parseDate($row['支払日']),
            'billing_date' => $this->parseDate($row['請求日'])
        ]);
    }

    public function rules(): array
    {
        return [
            '*.業者id' => ['required', 'integer'],
            '*.業者名' => ['required', 'string'],
            '*.建物名' => ['required', 'string'],
            '*.番号' => ['required', 'integer'],
            '*.受付内容' => ['required', 'string'],
            '*.支払金額' => ['required', 'integer'],
            '*.完工日' => ['required', 'date'],
            '*.支払日' => ['required', 'date'],
            '*.請求日' => ['required', 'date']
        ];
    }

    private function parseDate($date)
    {
        return Carbon::parse($date)->format('Y-m-d');
    }
}
