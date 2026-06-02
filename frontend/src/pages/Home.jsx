import ChatWindow from "../components/Chat/ChatWindow";
import { useChat } from "../context/ChatContext";
import useHealth from "../hooks/useHealth";

export default function Home() {
  const { chats, activeChat, activeChatId, setActiveChatId, createNewChat, sendMessage, renameChat, loading } = useChat();
  const health = useHealth();

  return (
    <div className="flex gap-3" style={{ height: "calc(100vh - 3rem)" }}>
      {/* Sessions panel */}
      <div className="w-[200px] min-w-[200px] card flex flex-col h-full">
        <div className="p-3 shrink-0" style={{ borderBottom: "1px solid var(--border)" }}>
          <button onClick={createNewChat} className="btn-accent w-full justify-center text-sm py-2.5">+ New Chat</button>
        </div>
        <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5 min-h-0 custom-scrollbar">
          {chats.map(chat => (
            <button key={chat.id} onClick={() => setActiveChatId(chat.id)}
              className="w-full text-left px-3 py-2.5 rounded-lg text-[13px] transition-all truncate"
              style={{
                background: activeChatId === chat.id ? "var(--accent-glow)" : "transparent",
                color: activeChatId === chat.id ? "var(--accent)" : "var(--text-muted)",
                borderLeft: activeChatId === chat.id ? "2px solid var(--accent)" : "2px solid transparent",
              }}>
              {chat.title || `Chat ${chat.id}`}
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 card overflow-hidden flex flex-col h-full">
        {/* Header */}
        <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border)" }}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "var(--accent)" }}>
              <span className="text-xs font-bold" style={{ color: "#0d0d0f" }}>AI</span>
            </div>
            <div>
              <p className="text-sm font-semibold" style={{ color: "var(--text-bright)" }}>Database Assistant</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Chat about your schema, write queries, explore data</p>
            </div>
          </div>
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-md text-[10px] mono" style={{ background: "var(--bg-surface)" }}>
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: health?.status === "ok" ? "var(--teal)" : "var(--accent)", animation: "glow 2s infinite" }}></div>
            <span style={{ color: "var(--text-muted)" }}>{health?.status?.toUpperCase() || "..."}</span>
          </div>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col min-h-0">
          <ChatWindow messages={activeChat?.messages || []} sendMessage={sendMessage} loading={loading} health={health} />
        </div>
      </div>
    </div>
  );
}
