import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import Loader from "../UI/Loader";
import { useTheme } from "../../context/ThemeContext";

export default function ChatWindow({ messages, sendMessage, loading, health }) {
  const messagesEndRef = useRef(null);
  const { isDark } = useTheme();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden transition-colors duration-300"
      style={{ background: "var(--bg-base)", color: "var(--text-primary)" }}>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-6 py-6 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-14 h-14 rounded-xl flex items-center justify-center mb-4"
              style={{ background: "var(--accent-glow)", border: "1px solid var(--border-active)" }}>
              <svg width="24" height="24" fill="none" stroke="var(--accent)" strokeWidth="1.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
              </svg>
            </div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-bright)" }}>
              Ask me anything
            </h3>
            <p className="text-sm max-w-md" style={{ color: "var(--text-secondary)" }}>
              Query your database, generate SQL, or explore schema documentation.
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
              {[
                '💡 "Show total revenue"',
                '📊 "Monthly trends"',
                '📖 "Describe customers table"',
                '🔍 "Top 10 sellers"',
              ].map(q => (
                <div key={q} className="px-4 py-2.5 rounded-lg cursor-pointer transition-all"
                  style={{ background: "var(--bg-raised)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--border-active)"; e.currentTarget.style.color = "var(--text-primary)"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-secondary)"; }}
                  onClick={() => sendMessage(q.replace(/[💡📊📖🔍] "/, "").replace(/"$/, ""))}>
                  {q}
                </div>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} isDark={isDark} />
        ))}

        {loading && <Loader isDark={isDark} />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="py-4 flex-shrink-0" style={{ borderTop: "1px solid var(--border)", background: "var(--bg-raised)" }}>
        <div className="max-w-3xl mx-auto px-4">
          <InputBox onSend={sendMessage} isDark={isDark} />
        </div>
      </div>
    </div>
  );
}
