<?php

namespace Tests\Feature;

use App\Models\Order;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Schema;
use Tests\TestCase;

class OrderControllerTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        // Configure test environment
        config([
            'database.default' => 'mysql',
            'database.connections.mysql.database' => 'testing',
            'database.connections.mysql.host' => 'mysql',
            'database.connections.mysql.username' => 'sail',
            'database.connections.mysql.password' => 'password'
        ]);

        // Run migrations
        $this->artisan('migrate:fresh');

        // Create and authenticate a user for testing
        $user = \App\Models\User::factory()->create();
        $this->actingAs($user);

        // Enable query logging
        DB::enableQueryLog();
    }

    protected function defineEnvironment($app)
    {
        // Session configuration for testing
        $app['config']->set('session.driver', 'array');
        $app['config']->set('session.lifetime', 120);
        $app['config']->set('session.expire_on_close', false);
    }

    protected function tearDown(): void
    {
        // Clean up database
        $this->artisan('migrate:fresh');
        
        parent::tearDown();
    }

    public function test_can_upload_valid_csv_file(): void
    {
        Log::debug('Starting test_can_upload_valid_csv_file');

        $filePath = base_path('tests/data/valid_orders.csv');
        Log::debug('Test file:', [
            'path' => $filePath,
            'exists' => file_exists($filePath),
            'content' => file_exists($filePath) ? file_get_contents($filePath) : null
        ]);

        $file = new UploadedFile(
            $filePath,
            'valid_orders.csv',
            'text/csv',
            null,
            true
        );

        $response = $this->withoutMiddleware()
            ->post('/orders/upload', [
                'file' => $file,
                'year_month' => '2025-02'
            ]);

        Log::debug('Response:', [
            'status' => $response->status(),
            'session' => session()->all(),
            'orders_count' => Order::count(),
            'all_orders' => Order::all()->toArray(),
            'query_log' => DB::getQueryLog()
        ]);

        $response->assertRedirect(route('orders.upload.form'));
        $response->assertSessionDoesntHaveErrors();
        $response->assertSessionHas('success', '2件のデータを取り込みました。1件のデータをスキップしました。');

        // Verify first order with all fields
        $order1 = Order::where([
            'vendor_id' => 1001,
            'vendor_name' => 'テスト業者1',
            'year_month' => '2025-02'
        ])->first();
        $this->assertNotNull($order1, 'First order was not created in database');
        $this->assertEquals(50000, $order1->payment_amount);
        $this->assertEquals('2025-02-01', $order1->completion_date->format('Y-m-d'));
        $this->assertEquals('2025-02-15', $order1->payment_date->format('Y-m-d'));
        $this->assertEquals('2025-02-10', $order1->billing_date->format('Y-m-d'));

        // Verify second order with special dates (2999-12-31) as null
        $order2 = Order::where([
            'vendor_id' => 1002,
            'vendor_name' => 'テスト業者2',
            'year_month' => '2025-02'
        ])->first();
        $this->assertNotNull($order2, 'Second order was not created in database');
        $this->assertEquals(0, $order2->payment_amount);
        $this->assertNull($order2->completion_date);
        $this->assertNull($order2->payment_date);
        $this->assertNull($order2->billing_date);

        // Verify vendor_id = 0 was skipped
        $this->assertEquals(0, Order::where('vendor_id', 0)->count());
    }

    public function test_cannot_upload_invalid_file()
    {
        $file = new UploadedFile(
            base_path('tests/data/invalid_orders.csv'),
            'invalid_orders.csv',
            'text/csv',
            null,
            true
        );

        $response = $this->from('/orders/upload')
            ->post('/orders/upload', [
                'file' => $file,
                'year_month' => '2025-02'
            ]);

        $response->assertRedirect('/orders/upload')
            ->assertSessionHasErrors('file');
    }

    public function test_validates_year_month_format()
    {
        $file = new UploadedFile(
            base_path('tests/data/valid_orders.csv'),
            'valid_orders.csv',
            'text/csv',
            null,
            true
        );

        $response = $this->post('/orders/upload', [
            'file' => $file,
            'year_month' => 'invalid-date'
        ]);

        $response->assertSessionHasErrors('year_month');
    }
}
