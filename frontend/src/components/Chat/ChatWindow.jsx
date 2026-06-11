import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import { useTheme } from "../../context/ThemeContext";

export default function ChatWindow({ messages, sendMessage, loading }) {
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
            {/* Animated waveform */}
            <div className="waveform mb-6">
              <span></span><span></span><span></span><span></span><span></span><span></span><span></span>
            </div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-bright)" }}>
              Ask me anything about your data
            </h3>
            <p className="text-sm max-w-md mb-1" style={{ color: "var(--text-secondary)" }}>
              Query your database, generate SQL, or explore schema documentation.
            </p>
            <p className="text-xs max-w-md mb-6" style={{ color: "var(--text-muted)" }}>
              I can write queries, analyze trends, and explain your schema.
            </p>
            <div className="grid grid-cols-2 gap-3 text-sm max-w-lg">
              {[
                { emoji: "💡", q: "Show total revenue" },
                { emoji: "📊", q: "Monthly trends" },
                { emoji: "📖", q: "Describe customers table" },
                { emoji: "🔍", q: "Top 10 sellers" },
              ].map(item => (
                <div key={item.q} className="px-4 py-3 rounded-lg cursor-pointer transition-all duration-200 flex items-center gap-2.5"
                  style={{ background: "var(--bg-raised)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--border-active)"; e.currentTarget.style.color = "var(--text-primary)"; e.currentTarget.style.transform = "translateY(-1px)"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-secondary)"; e.currentTarget.style.transform = "translateY(0)"; }}
                  onClick={() => sendMessage(item.q)}>
                  <span className="text-base">{item.emoji}</span>
                  <span className="text-[13px]">{item.q}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} isDark={isDark} />
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex items-start gap-3 rise">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: "var(--accent-glow)", border: "1px solid var(--border-active)" }}>
              <span className="text-xs">✨</span>
            </div>
            <div className="card px-4 py-3 rounded-2xl" style={{ borderTopLeftRadius: 4 }}>
              <div className="typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
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
