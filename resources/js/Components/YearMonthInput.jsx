import { forwardRef } from 'react';
import TextInput from '@/Components/TextInput';
import InputLabel from '@/Components/InputLabel';
import InputError from '@/Components/InputError';

const YearMonthInput = forwardRef(({ label, error, className = '', ...props }, ref) => {
    return (
        <div>
            <InputLabel htmlFor="year_month" value={label} />
            <TextInput
                id="year_month"
                type="text"
                pattern="\d{4}-\d{2}"
                placeholder="2025-02"
                className={`mt-1 block w-full ${className}`}
                ref={ref}
                {...props}
            />
            <InputError message={error} className="mt-2" />
        </div>
    );
});

YearMonthInput.displayName = 'YearMonthInput';

export default YearMonthInput;
