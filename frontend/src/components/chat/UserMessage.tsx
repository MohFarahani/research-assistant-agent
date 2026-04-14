import type { UserMessage as UserMessageType } from "@/types/chat";

interface UserMessageProps {
  message: UserMessageType;
}

export function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex justify-end mb-4 px-4">
      <div className="max-w-[70%] rounded-2xl rounded-tr-sm px-4 py-3 bg-zinc-600 text-zinc-100 text-sm leading-relaxed break-words whitespace-pre-wrap">
        {message.content}
      </div>
    </div>
  );
}
