import { Head, useForm } from '@inertiajs/react';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import YearMonthInput from '@/Components/YearMonthInput';
import FileInput from '@/Components/FileInput';
import SubmitButton from '@/Components/SubmitButton';

export default function Upload({ flash }) {
    const { data, setData, post, processing, errors, reset } = useForm({
        year_month: '',
        file: null,
    });

    const handleSubmit = (e) => {
        e.preventDefault();
        post(route('orders.upload'), {
            onSuccess: () => {
                reset('file');
            },
        });
    };

    return (
        <AuthenticatedLayout
            header={<h2 className="text-xl font-semibold leading-tight text-gray-800">発注一覧アップロード</h2>}
        >
            <Head title="発注一覧アップロード" />
            <div className="py-12">
                <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
                    <div className="overflow-hidden bg-white shadow-sm sm:rounded-lg">
                        <div className="p-6">
                            {flash?.success && (
                                <div className="mb-4 rounded bg-green-100 p-4 text-green-700">
                                    {flash.success}
                                </div>
                            )}
                            {errors.file && (
                                <div className="mb-4 rounded bg-red-100 p-4 text-red-700">
                                    {errors.file}
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className="space-y-6">
                                <YearMonthInput
                                    label="年月 (YYYY-MM)"
                                    value={data.year_month}
                                    onChange={e => setData('year_month', e.target.value)}
                                    error={errors.year_month}
                                    required
                                />

                                <FileInput
                                    label="発注書一覧エクセル"
                                    onChange={e => setData('file', e.target.files[0])}
                                    error={errors.file}
                                    accept=".xlsx,.csv"
                                    required
                                    helpText={
                                        <>
                                            ファイルサイズ上限: 1MB<br />
                                            対応形式: Excel (.xlsx), CSV (.csv)
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
