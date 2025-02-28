<?php

namespace App\Services;

use App\Models\Order;
use Illuminate\Database\Eloquent\Builder;

class OrderSearchService
{
    public function applyFilters(Builder $query, array $filters): Builder
    {
        if (!empty($filters['year_month'])) {
            $query = $this->filterByYearMonth($query, $filters['year_month']);
        }
        
        if (!empty($filters['vendor_name'])) {
            $query = $this->filterByVendorName($query, $filters['vendor_name']);
        }
        
        return $query;
    }
    
    private function filterByYearMonth(Builder $query, string $yearMonth): Builder
    {
        return $query->where('year_month', 'like', '%' . $yearMonth . '%');
    }
    
    private function filterByVendorName(Builder $query, string $vendorName): Builder
    {
        return $query->where('vendor_name', 'like', '%' . $vendorName . '%');
    }
}
