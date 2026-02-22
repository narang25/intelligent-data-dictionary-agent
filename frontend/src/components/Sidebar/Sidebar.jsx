import { useState } from "react";
import ChatItem from "./ChatItem";
import { useTheme } from "../../context/ThemeContext";

export default function Sidebar({
  chats,
  activeChatId,
  setActiveChatId,
  createNewChat,
  renameChat
}) {
  const [search, setSearch] = useState("");
  const { isDark, toggleTheme } = useTheme();

  const filteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={`h-full flex flex-col border-r transition-colors duration-300 ${
      isDark 
        ? "bg-neutral-950 text-neutral-200 border-neutral-800" 
        : "bg-gray-50 text-gray-800 border-gray-200"
    }`}>

      {/* Header with Theme Toggle */}
      <div className={`p-3 border-b ${isDark ? "border-neutral-800" : "border-gray-200"}`}>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider opacity-60">
            Chats
          </span>
          
          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-lg transition-colors ${
              isDark 
                ? "hover:bg-neutral-800 text-yellow-400" 
                : "hover:bg-gray-200 text-gray-600"
            }`}
            title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {isDark ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
        </div>

        {/* New Chat Button */}
        <button
          onClick={createNewChat}
          className={`w-full p-2.5 rounded-lg transition-colors text-sm font-medium flex items-center justify-center gap-2 ${
            isDark 
              ? "bg-blue-600 hover:bg-blue-500 text-white" 
              : "bg-blue-500 hover:bg-blue-600 text-white"
          }`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Search */}
      <div className="p-3">
        <input
          type="text"
          placeholder="Search chats..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={`w-full px-3 py-2 text-sm rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            isDark 
              ? "bg-neutral-900 text-neutral-200 placeholder-neutral-500" 
              : "bg-white text-gray-800 placeholder-gray-400 border border-gray-200"
          }`}
        />
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1 min-h-0">
        {filteredChats.length === 0 ? (
          <div className={`text-center py-8 text-sm ${isDark ? "text-neutral-500" : "text-gray-400"}`}>
            No chats found
          </div>
        ) : (
          filteredChats.map(chat => (
            <ChatItem
              key={chat.id}
              chat={chat}
              isActive={chat.id === activeChatId}
              onClick={() => setActiveChatId(chat.id)}
              onRename={(newTitle) => renameChat(chat.id, newTitle)}
              isDark={isDark}
            />
          ))
        )}
      </div>
    </div>
  );
}
