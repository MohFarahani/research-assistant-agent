import { useRef } from "react";
import { UploadIcon, SpinnerIcon } from "@/components/icons";

interface UploadButtonProps {
  onUpload: (file: File) => void;
  isPending: boolean;
  isRateLimited?: boolean;
  resetTime?: string;
}

export function UploadButton({ onUpload, isPending, isRateLimited = false, resetTime }: UploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = "";
    }
  };

  const disabled = isPending || isRateLimited;

  return (
    <div className="space-y-2">
      {isRateLimited && (
        <div className="flex items-start gap-2 px-3 py-2 bg-red-950/60 border border-red-800/60 rounded-lg text-xs text-red-300">
          <svg className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>
            Daily limit reached. Uploads are disabled
            {resetTime ? <> until <span className="font-medium text-red-200">{resetTime}</span></> : ""}.
          </span>
        </div>
      )}
      <label
        htmlFor="file-upload"
        aria-disabled={disabled}
        className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-xl transition-colors duration-150 select-none ${
          disabled
            ? "opacity-50 cursor-not-allowed pointer-events-none"
            : "hover:bg-blue-500 active:bg-blue-700 cursor-pointer focus-within:ring-2 focus-within:ring-blue-400"
        }`}
      >
        <input
          ref={inputRef}
          id="file-upload"
          type="file"
          accept=".pdf,.doc,.docx,.txt"
          onChange={handleChange}
          disabled={disabled}
          className="sr-only"
        />
        {isPending ? (
          <>
            <SpinnerIcon className="w-4 h-4 animate-spin" />
            <span>Uploading...</span>
          </>
        ) : (
          <>
            <UploadIcon className="w-4 h-4" />
            <span>Upload New Document</span>
          </>
        )}
      </label>
    </div>
  );
}
