import { useState } from 'react';
import { Head, useForm } from '@inertiajs/react';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';

export default function Upload() {
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
                                <div>
                                    <label htmlFor="year_month" className="block text-sm font-medium text-gray-700">
                                        年月 (YYYY-MM)
                                    </label>
                                    <input
                                        type="text"
                                        id="year_month"
                                        pattern="\d{4}-\d{2}"
                                        placeholder="2025-02"
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                        value={data.year_month}
                                        onChange={e => setData('year_month', e.target.value)}
                                        required
                                    />
                                    {errors.year_month && (
                                        <p className="mt-2 text-sm text-red-600">{errors.year_month}</p>
                                    )}
                                </div>

                                <div>
                                    <label htmlFor="file" className="block text-sm font-medium text-gray-700">
                                        発注書一覧エクセル
                                    </label>
                                    <input
                                        type="file"
                                        id="file"
                                        accept=".xlsx,.csv"
                                        className="mt-1 block w-full"
                                        onChange={e => setData('file', e.target.files[0])}
                                        required
                                    />
                                    <p className="mt-2 text-sm text-gray-500">
                                        ファイルサイズ上限: 1MB<br />
                                        対応形式: Excel (.xlsx), CSV (.csv)
                                    </p>
                                </div>

                                <div className="flex justify-center">
                                    <button
                                        type="submit"
                                        disabled={processing}
                                        className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
                                    >
                                        {processing ? 'アップロード中...' : 'アップロード'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </AuthenticatedLayout>
    );
}
