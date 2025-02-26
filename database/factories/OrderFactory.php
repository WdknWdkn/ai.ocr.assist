<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

class OrderFactory extends Factory
{
    public function definition(): array
    {
        return [
            'year_month' => $this->faker->date('Y-m'),
            'vendor_id' => $this->faker->numberBetween(1000, 9999),
            'vendor_name' => $this->faker->company(),
            'building_name' => $this->faker->buildingNumber(),
            'number' => $this->faker->numberBetween(1, 100),
            'reception_details' => $this->faker->sentence(),
            'payment_amount' => $this->faker->numberBetween(1000, 100000),
            'completion_date' => $this->faker->date(),
            'payment_date' => $this->faker->date(),
            'billing_date' => $this->faker->date(),
            'erase_flg' => $this->faker->boolean(),
        ];
    }
}
