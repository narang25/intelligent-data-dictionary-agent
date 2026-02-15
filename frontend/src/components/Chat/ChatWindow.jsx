import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import Loader from "../UI/Loader";

export default function ChatWindow({
  messages,
  sendMessage,
  loading,
  health,
}) {
  const getHealthColor = () => {
    if (!health) return "bg-yellow-500";
    if (health.status === "ok") return "bg-green-500";
    if (health.status === "degraded") return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="flex-1 flex flex-col bg-neutral-900 text-neutral-200 min-h-0">

      {/* Header */}
      <div className="p-4 border-b border-neutral-800 flex justify-between items-center text-sm">
        <div className="font-medium">
          Intelligent Data Dictionary
        </div>

        <div className="flex items-center gap-2 text-xs">
          <div
            className={`w-2 h-2 rounded-full ${getHealthColor()}`}
          />
          <span>
            {health?.status?.toUpperCase() || "CHECKING"}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 min-h-0">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {loading && <Loader />}
      </div>

      {/* Input */}
      <div className="border-t border-neutral-800 bg-neutral-900 py-4">
        <div className="max-w-3xl mx-auto px-4">
          <InputBox onSend={sendMessage} />
        </div>
      </div>
    </div>
  );
}
