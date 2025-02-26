<?php

namespace Tests\Feature;

use App\Models\Order;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class OrderListTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        $this->user = User::factory()->create();
        $this->actingAs($this->user);
    }

    public function test_can_view_orders_list()
    {
        $orders = Order::factory()->count(3)->create([
            'year_month' => '2025-02',
            'vendor_name' => 'テスト業者A'
        ]);

        $response = $this->get(route('orders.index'));

        $response->assertStatus(200);
        $response->assertInertia(fn ($assert) => $assert
            ->component('Orders/Index')
            ->has('orders.data', 3)
            ->has('filters', fn ($assert) => $assert
                ->missing('year_month')
                ->missing('vendor_name')
            )
        );
    }

    public function test_can_search_orders_by_vendor_name()
    {
        Order::factory()->create([
            'year_month' => '2025-02',
            'vendor_name' => 'テスト業者A'
        ]);
        Order::factory()->create([
            'year_month' => '2025-02',
            'vendor_name' => 'テスト業者B'
        ]);

        $response = $this->get(route('orders.index', [
            'vendor_name' => 'A'
        ]));

        $response->assertStatus(200);
        $response->assertInertia(fn ($assert) => $assert
            ->component('Orders/Index')
            ->has('orders.data', 1)
            ->where('orders.data.0.vendor_name', 'テスト業者A')
            ->has('filters', fn ($assert) => $assert
                ->where('vendor_name', 'A')
            )
        );
    }

    public function test_can_search_orders_by_year_month()
    {
        Order::factory()->create([
            'year_month' => '2025-01',
            'vendor_name' => 'テスト業者A'
        ]);
        Order::factory()->create([
            'year_month' => '2025-02',
            'vendor_name' => 'テスト業者A'
        ]);

        $response = $this->get(route('orders.index', [
            'year_month' => '2025-01'
        ]));

        $response->assertStatus(200);
        $response->assertInertia(fn ($assert) => $assert
            ->component('Orders/Index')
            ->has('orders.data', 1)
            ->where('orders.data.0.year_month', '2025-01')
            ->has('filters', fn ($assert) => $assert
                ->where('year_month', '2025-01')
            )
        );
    }
}
