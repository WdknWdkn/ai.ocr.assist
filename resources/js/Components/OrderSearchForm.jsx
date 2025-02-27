import { useForm } from '@inertiajs/react';
import TextInput from '@/Components/TextInput';
import SubmitButton from '@/Components/SubmitButton';

export default function OrderSearchForm({ filters }) {
    const { data, setData, get } = useForm({
        year_month: filters.year_month || '',
        vendor_name: filters.vendor_name || ''
    });

    const handleSearch = (e) => {
        e.preventDefault();
        get(route('orders.index'));
    };

    return (
        <form onSubmit={handleSearch} className="mb-6 flex gap-4">
            <TextInput
                type="text"
                value={data.year_month}
                onChange={e => setData('year_month', e.target.value)}
                placeholder="年月"
                className="rounded border px-3 py-2"
            />
            <TextInput
                type="text"
                value={data.vendor_name}
                onChange={e => setData('vendor_name', e.target.value)}
                placeholder="業者名"
                className="rounded border px-3 py-2"
            />
            <SubmitButton>検索</SubmitButton>
        </form>
    );
}
