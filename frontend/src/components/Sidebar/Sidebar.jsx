import ChatItem from "./ChatItem";

export default function Sidebar({
  chats,
  activeChatId,
  setActiveChatId,
  createNewChat
}) {
  return (
    <div className="h-full flex flex-col bg-neutral-950 text-neutral-200 border-r border-neutral-800">

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={createNewChat}
          className="w-full p-2 bg-neutral-900 rounded-lg hover:bg-neutral-800 transition text-sm"
        >
          + New Chat
        </button>
      </div>

      {/* Scrollable Chat List */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1 min-h-0">
        {chats.map(chat => (
          <ChatItem
            key={chat.id}
            chat={chat}
            isActive={chat.id === activeChatId}
            onClick={() => setActiveChatId(chat.id)}
          />
        ))}
      </div>
    </div>
  );
}
