import { useState } from "react";
import ChatItem from "./ChatItem";

export default function Sidebar({
  chats,
  activeChatId,
  setActiveChatId,
  createNewChat,
  renameChat
}) {
  const [search, setSearch] = useState("");

  const filteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-neutral-950 text-neutral-200 border-r border-neutral-800">

      {/* New Chat Button */}
      <div className="p-3 space-y-3">
        <button
          onClick={createNewChat}
          className="w-full p-2 bg-neutral-900 rounded-lg hover:bg-neutral-800 transition text-sm"
        >
          + New Chat
        </button>

        {/* Search */}
        <input
          type="text"
          placeholder="Search chats..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 text-sm bg-neutral-900 rounded-lg focus:outline-none"
        />
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1 min-h-0">
        {filteredChats.map(chat => (
          <ChatItem
            key={chat.id}
            chat={chat}
            isActive={chat.id === activeChatId}
            onClick={() => setActiveChatId(chat.id)}
            onRename={(newTitle) => renameChat(chat.id, newTitle)}
          />
        ))}
      </div>
    </div>
  );
}
