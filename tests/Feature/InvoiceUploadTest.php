<?php

namespace Tests\Feature;

use Tests\TestCase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use App\Models\User;

class InvoiceUploadTest extends TestCase
{
    public function setUp(): void
    {
        parent::setUp();
        $this->user = User::factory()->create();
    }

    public function test_can_view_upload_form()
    {
        $response = $this->actingAs($this->user)
            ->get(route('invoices.upload.form'));
        
        $response->assertStatus(200);
        $response->assertInertia(fn ($assert) => $assert
            ->component('Invoices/Upload')
        );
    }

    public function test_can_upload_pdf()
    {
        Storage::fake('local');
        
        $file = UploadedFile::fake()->create('invoice.pdf', 100);
        
        $response = $this->actingAs($this->user)
            ->post(route('invoices.upload'), [
                'file' => $file
            ]);
            
        $response->assertRedirect();
        $response->assertSessionHas('success');
    }

    public function test_validates_file_type()
    {
        Storage::fake('local');
        
        $file = UploadedFile::fake()->create('invoice.txt', 100);
        
        $response = $this->actingAs($this->user)
            ->post(route('invoices.upload'), [
                'file' => $file
            ]);
            
        $response->assertRedirect();
        $response->assertSessionHasErrors('file');
    }

    public function test_validates_file_size()
    {
        Storage::fake('local');
        
        $file = UploadedFile::fake()->create('invoice.pdf', 2048); // 2MB
        
        $response = $this->actingAs($this->user)
            ->post(route('invoices.upload'), [
                'file' => $file
            ]);
            
        $response->assertRedirect();
        $response->assertSessionHasErrors('file');
    }
}
