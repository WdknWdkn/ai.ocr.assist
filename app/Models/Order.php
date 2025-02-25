<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Concerns\HasTimestamps;

class Order extends Model
{
    use HasFactory;
    use HasTimestamps;

    protected $fillable = [
        'year_month',
        'vendor_id',
        'vendor_name',
        'building_name',
        'number',
        'reception_details',
        'payment_amount',
        'completion_date',
        'payment_date',
        'billing_date',
        'erase_flg'
    ];

    protected $casts = [
        'vendor_id' => 'integer',
        'number' => 'integer',
        'payment_amount' => 'integer',
        'completion_date' => 'date',
        'payment_date' => 'date',
        'billing_date' => 'date',
        'erase_flg' => 'boolean'
    ];
}
