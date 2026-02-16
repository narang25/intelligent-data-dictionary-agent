import { useState, useEffect } from "react";

export default function ChatItem({
  chat,
  isActive,
  onClick,
  onRename
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
      className={`p-2 rounded-md cursor-pointer text-sm truncate transition ${
        isActive
          ? "bg-neutral-800"
          : "hover:bg-neutral-800"
      }`}
      onClick={() => !editing && onClick()}
    >
      {editing ? (
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleRename();
            if (e.key === "Escape") setEditing(false);
          }}
          className="w-full bg-neutral-700 px-2 py-1 rounded text-xs focus:outline-none"
          autoFocus
        />
      ) : (
        <div
          onDoubleClick={(e) => {
            e.stopPropagation();
            setEditing(true);
          }}
        >
          {chat.title}
        </div>
      )}
    </div>
  );
}
