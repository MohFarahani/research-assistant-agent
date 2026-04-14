import { useRef } from "react";
import { UploadIcon, SpinnerIcon } from "@/components/icons";

interface UploadButtonProps {
  onUpload: (file: File) => void;
  isPending: boolean;
}

export function UploadButton({ onUpload, isPending }: UploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = "";
    }
  };

  return (
    <label
      htmlFor="file-upload"
      aria-disabled={isPending}
      className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-sm font-medium rounded-xl cursor-pointer transition-colors duration-150 focus-within:ring-2 focus-within:ring-blue-400 select-none ${isPending ? "opacity-60 pointer-events-none" : ""}`}
    >
      <input
        ref={inputRef}
        id="file-upload"
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        onChange={handleChange}
        disabled={isPending}
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
  );
}
