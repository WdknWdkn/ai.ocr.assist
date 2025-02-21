import PrimaryButton from '@/Components/PrimaryButton';

export default function SubmitButton({ 
    children, 
    processing, 
    processingText,
    className = '', 
    ...props 
}) {
    return (
        <PrimaryButton
            type="submit"
            disabled={processing}
            className={`justify-center ${className}`}
            {...props}
        >
            {processing ? processingText : children}
        </PrimaryButton>
    );
}
