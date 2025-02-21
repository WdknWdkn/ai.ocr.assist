import { forwardRef } from 'react';
import InputLabel from '@/Components/InputLabel';
import InputError from '@/Components/InputError';

const FileInput = forwardRef(({ label, error, accept, helpText, className = '', ...props }, ref) => {
    return (
        <div>
            <InputLabel htmlFor="file" value={label} />
            <input
                type="file"
                className={`mt-1 block w-full ${className}`}
                ref={ref}
                accept={accept}
                {...props}
            />
            {helpText && (
                <p className="mt-2 text-sm text-gray-500">{helpText}</p>
            )}
            <InputError message={error} className="mt-2" />
        </div>
    );
});

FileInput.displayName = 'FileInput';

export default FileInput;
