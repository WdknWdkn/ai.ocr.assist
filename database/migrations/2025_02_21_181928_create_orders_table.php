<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('orders', function (Blueprint $table) {
            $table->id();
            $table->string('year_month')->comment('年月');
            $table->integer('vendor_id')->comment('業者ID');
            $table->string('vendor_name')->comment('業者名');
            $table->string('building_name')->comment('建物名');
            $table->integer('number')->comment('番号');
            $table->string('reception_details')->comment('受付内容');
            $table->integer('payment_amount')->comment('支払金額');
            $table->date('completion_date')->comment('完工日');
            $table->date('payment_date')->comment('支払日');
            $table->date('billing_date')->comment('請求日');
            $table->timestamp('created_at')->comment('登録日')->nullable();
            $table->timestamp('updated_at')->comment('更新日')->nullable();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('orders');
    }
};
