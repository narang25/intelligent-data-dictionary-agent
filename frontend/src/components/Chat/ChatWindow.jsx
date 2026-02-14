import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";

export default function ChatWindow({ messages, sendMessage }) {
  return (
    <div className="flex-1 flex flex-col bg-neutral-900 text-neutral-200 min-h-0">

      {/* Header */}
      <div className="p-4 border-b border-neutral-800 font-medium text-sm">
        Intelligent Data Dictionary
      </div>

      {/* Scrollable Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 min-h-0">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>

      {/* Centered Input */}
      <div className="border-t border-neutral-800 bg-neutral-900 py-4">
        <div className="max-w-3xl mx-auto px-4">
          <InputBox onSend={sendMessage} />
        </div>
      </div>
    </div>
  );
}
