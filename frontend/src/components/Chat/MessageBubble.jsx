export default function MessageBubble({ message }) {
  const isUser = message.sender === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`px-4 py-2 rounded-lg max-w-[70%] text-sm ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-neutral-800 text-neutral-200"
        }`}
      >
        {message.text}
      </div>
    </div>
  );
}
