<?php

namespace Tests\Feature;

use App\Models\Order;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Log;
use Tests\TestCase;

class OrderControllerTest extends TestCase
{
    use RefreshDatabase;

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
        
        // Create and authenticate a user for testing
        $user = \App\Models\User::factory()->create();
        $this->actingAs($user);
    }

    protected function defineEnvironment($app)
    {
        // Session configuration for testing
        $app['config']->set('session.driver', 'array');
        $app['config']->set('session.lifetime', 120);
        $app['config']->set('session.expire_on_close', false);
    }

    public function test_can_upload_valid_csv_file()
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
            'year_month' => '2025-02'
        ]);

        $response->assertRedirect();
        
        Log::debug('Response:', [
            'status' => $response->status(),
            'session' => $response->getSession()->all(),
            'errors' => $response->getSession()->get('errors')
        ]);
        
        // Check database state
        $orders = Order::all();
        Log::debug('Database state:', [
            'count' => $orders->count(),
            'orders' => $orders->toArray()
        ]);
        
        $order = Order::where([
            'vendor_id' => '1001',
            'vendor_name' => 'テスト業者1',
            'year_month' => '2025-02'
        ])->first();
        
        $this->assertNotNull($order, 'Order was not created in database');
        $this->assertDatabaseHas('orders', [
            'vendor_id' => '1001',
            'vendor_name' => 'テスト業者1',
            'year_month' => '2025-02'
        ]);
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
