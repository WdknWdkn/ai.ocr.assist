import { Head, useForm, Link } from '@inertiajs/react';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import {
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    flexRender,
} from '@tanstack/react-table';
import { useState } from 'react';

const columns = [
    { header: '年月', accessorKey: 'year_month' },
    { header: '業者ID', accessorKey: 'vendor_id' },
    { header: '業者名', accessorKey: 'vendor_name' },
    { header: '建物名', accessorKey: 'building_name' },
    { header: '番号', accessorKey: 'number' },
    { header: '受付内容', accessorKey: 'reception_details' },
    { 
        header: '支払金額',
        accessorKey: 'payment_amount',
        cell: ({ row }) => new Intl.NumberFormat('ja-JP').format(row.original.payment_amount)
    },
    { 
        header: '照合完了',
        accessorKey: 'erase_flg',
        cell: ({ row }) => row.original.erase_flg ? '完了' : '未完了'
    }
];

export default function Index({ orders, filters }) {
    const [sorting, setSorting] = useState([]);
    const { data, setData, get } = useForm({
        year_month: filters.year_month || '',
        vendor_name: filters.vendor_name || ''
    });

    const table = useReactTable({
        data: orders.data,
        columns,
        state: { sorting },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
    });

    const handleSearch = (e) => {
        e.preventDefault();
        get(route('orders.index'));
    };

    return (
        <AuthenticatedLayout
            header={<h2 className="text-xl font-semibold leading-tight text-gray-800">発注一覧</h2>}
        >
            <Head title="発注一覧" />
            <div className="py-12">
                <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
                    <div className="overflow-hidden bg-white shadow-sm sm:rounded-lg">
                        <div className="p-6">
                            <form onSubmit={handleSearch} className="mb-6 flex gap-4">
                                <input
                                    type="text"
                                    value={data.year_month}
                                    onChange={e => setData('year_month', e.target.value)}
                                    placeholder="年月"
                                    className="rounded border px-3 py-2"
                                />
                                <input
                                    type="text"
                                    value={data.vendor_name}
                                    onChange={e => setData('vendor_name', e.target.value)}
                                    placeholder="業者名"
                                    className="rounded border px-3 py-2"
                                />
                                <button
                                    type="submit"
                                    className="rounded bg-gray-800 px-4 py-2 text-white hover:bg-gray-700"
                                >
                                    検索
                                </button>
                            </form>

                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        {table.getHeaderGroups().map(headerGroup => (
                                            <tr key={headerGroup.id}>
                                                {headerGroup.headers.map(header => (
                                                    <th
                                                        key={header.id}
                                                        onClick={header.column.getToggleSortingHandler()}
                                                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                                    >
                                                        {flexRender(
                                                            header.column.columnDef.header,
                                                            header.getContext()
                                                        )}
                                                    </th>
                                                ))}
                                            </tr>
                                        ))}
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {table.getRowModel().rows.map(row => (
                                            <tr key={row.id}>
                                                {row.getVisibleCells().map(cell => (
                                                    <td
                                                        key={cell.id}
                                                        className="px-6 py-4 whitespace-nowrap"
                                                    >
                                                        {flexRender(
                                                            cell.column.columnDef.cell,
                                                            cell.getContext()
                                                        )}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {orders.links && (
                                <div className="mt-4 flex justify-between">
                                    {orders.links.map((link, i) => (
                                        <Link
                                            key={i}
                                            href={link.url}
                                            className={`px-4 py-2 border rounded ${
                                                link.active
                                                    ? 'bg-gray-800 text-white'
                                                    : 'text-gray-700'
                                            }`}
                                            dangerouslySetInnerHTML={{ __html: link.label }}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </AuthenticatedLayout>
    );
}
