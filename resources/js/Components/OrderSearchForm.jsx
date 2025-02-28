import { useForm } from '@inertiajs/react';
import TextInput from '@/Components/TextInput';
import SubmitButton from '@/Components/SubmitButton';
import InputLabel from '@/Components/InputLabel';
import InputError from '@/Components/InputError';

export default function OrderSearchForm({ filters }) {
    const { data, setData, get, errors, processing } = useForm({
        year_month: filters.year_month || '',
        vendor_name: filters.vendor_name || ''
    });

    const handleSearch = (e) => {
        e.preventDefault();
        get(route('orders.index'));
    };

    return (
        <form onSubmit={handleSearch} className="mb-6 space-y-4">
            <div className="flex gap-4">
                <div>
                    <InputLabel htmlFor="year_month" value="年月" />
                    <TextInput
                        id="year_month"
                        type="text"
                        className="mt-1 block"
                        value={data.year_month}
                        onChange={e => setData('year_month', e.target.value)}
                        placeholder="YYYY-MM"
                    />
                    <InputError className="mt-2" message={errors.year_month} />
                </div>

                <div>
                    <InputLabel htmlFor="vendor_name" value="業者名" />
                    <TextInput
                        id="vendor_name"
                        type="text"
                        className="mt-1 block"
                        value={data.vendor_name}
                        onChange={e => setData('vendor_name', e.target.value)}
                        placeholder="業者名を入力"
                    />
                    <InputError className="mt-2" message={errors.vendor_name} />
                </div>

                <div className="flex items-end">
                    <SubmitButton processing={processing}>検索</SubmitButton>
                </div>
            </div>
        </form>
    );
}
