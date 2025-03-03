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
        
        // Create a PDF file with some content
        $pdfPath = storage_path('app/test.pdf');
        $pdf = new \FPDF();
        $pdf->AddPage();
        $pdf->SetFont('Arial', '', 12);
        $pdf->Cell(0, 10, 'Test Invoice', 0, 1, 'C');
        $pdf->Cell(0, 10, '請求書テスト', 0, 1, 'C');
        $pdf->Output($pdfPath, 'F');
        
        $file = new UploadedFile(
            $pdfPath,
            'invoice.pdf',
            'application/pdf',
            null,
            true
        );
        
        $response = $this->actingAs($this->user)
            ->post(route('invoices.upload'), [
                'file' => $file
            ]);
            
        $response->assertRedirect();
        $response->assertSessionHas('success');
        
        unlink($pdfPath);
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
