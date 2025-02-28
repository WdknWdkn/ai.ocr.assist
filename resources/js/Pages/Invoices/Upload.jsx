import { Head, useForm } from '@inertiajs/react';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import FileInput from '@/Components/FileInput';
import SubmitButton from '@/Components/SubmitButton';

export default function Upload({ flash }) {
    const { data, setData, post, processing, errors, reset } = useForm({
        file: null,
    });

    const handleSubmit = (e) => {
        e.preventDefault();
        post(route('invoices.upload'), {
            onSuccess: () => {
                reset('file');
            },
        });
    };

    return (
        <AuthenticatedLayout
            header={<h2 className="text-xl font-semibold leading-tight text-gray-800">請求書アップロード</h2>}
        >
            <Head title="請求書アップロード" />
            <div className="py-12">
                <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
                    <div className="overflow-hidden bg-white shadow-sm sm:rounded-lg">
                        <div className="p-6">
                            {flash?.success && (
                                <div className="mb-4 rounded bg-green-100 p-4 text-green-700">
                                    {flash.success}
                                </div>
                            )}
                            {flash?.invoice_data && (
                                <div className="mb-4 rounded bg-blue-100 p-4 text-blue-700">
                                    <h3 className="font-semibold mb-2">解析結果:</h3>
                                    <pre className="whitespace-pre-wrap">
                                        {JSON.stringify(flash.invoice_data, null, 2)}
                                    </pre>
                                </div>
                            )}
                            {errors.file && (
                                <div className="mb-4 rounded bg-red-100 p-4 text-red-700">
                                    {errors.file}
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className="space-y-6">
                                <FileInput
                                    label="請求書PDF/画像"
                                    onChange={e => setData('file', e.target.files[0])}
                                    error={errors.file}
                                    accept=".pdf,.jpg,.jpeg,.png"
                                    required
                                    helpText={
                                        <>
                                            ファイルサイズ上限: 1MB<br />
                                            対応形式: PDF (.pdf), 画像 (.jpg, .png)
                                        </>
                                    }
                                />

                                <div className="flex justify-center">
                                    <SubmitButton
                                        processing={processing}
                                        processingText="アップロード中..."
                                    >
                                        アップロード
                                    </SubmitButton>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </AuthenticatedLayout>
    );
}
