<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Order extends Model
{
    use HasFactory;

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
        'billing_date'
    ];

    protected $casts = [
        'completion_date' => 'date',
        'payment_date' => 'date',
        'billing_date' => 'date'
    ];
}
