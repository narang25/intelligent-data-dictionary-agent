import { useState, useEffect } from "react";

export default function ChatItem({
  chat,
  isActive,
  onClick,
  onRename,
  isDark = true
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(chat.title);

  useEffect(() => {
    setTitle(chat.title);
  }, [chat.title]);

  const handleRename = () => {
    if (!title.trim()) return;
    if (onRename) {
      onRename(title.trim());
    }
    setEditing(false);
  };

  return (
    <div
      className={`p-2.5 rounded-lg cursor-pointer text-sm truncate transition-colors flex items-center gap-2 ${
        isActive
          ? isDark 
            ? "bg-neutral-800 text-white" 
            : "bg-blue-100 text-blue-800"
          : isDark
            ? "hover:bg-neutral-800/50 text-neutral-300"
            : "hover:bg-gray-100 text-gray-700"
      }`}
      onClick={() => !editing && onClick()}
    >
      {/* Chat Icon */}
      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 flex-shrink-0 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>

      {editing ? (
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleRename();
            if (e.key === "Escape") setEditing(false);
          }}
          className={`flex-1 px-2 py-1 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 ${
            isDark 
              ? "bg-neutral-700 text-white" 
              : "bg-white text-gray-800 border border-gray-300"
          }`}
          autoFocus
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <div
          className="flex-1 truncate"
          onDoubleClick={(e) => {
            e.stopPropagation();
            setEditing(true);
          }}
          title={chat.title}
        >
          {chat.title}
        </div>
      )}
    </div>
  );
}
