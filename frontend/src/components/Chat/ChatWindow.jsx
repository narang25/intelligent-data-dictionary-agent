import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import Loader from "../UI/Loader";
import { useTheme } from "../../context/ThemeContext";

export default function ChatWindow({
  messages,
  sendMessage,
  loading,
  health,
}) {
  const messagesEndRef = useRef(null);
  const { isDark } = useTheme();

  // Auto-scroll to bottom when messages change or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const getHealthColor = () => {
    if (!health) return "bg-yellow-500";
    if (health.status === "ok") return "bg-green-500";
    if (health.status === "degraded") return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className={`flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden transition-colors duration-300 ${
      isDark ? "bg-neutral-900 text-neutral-200" : "bg-white text-gray-800"
    }`}>

      {/* Header */}
      <div className={`p-4 border-b flex justify-between items-center text-sm flex-shrink-0 ${
        isDark ? "border-neutral-800" : "border-gray-200"
      }`}>
        <div className="flex items-center gap-3">
          {/* Logo/Icon */}
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
            isDark ? "bg-blue-600" : "bg-blue-500"
          }`}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
          </div>
          <div>
            <div className="font-semibold">Intelligent Data Dictionary</div>
            <div className={`text-xs ${isDark ? "text-neutral-400" : "text-gray-500"}`}>
              AI-Powered Database Assistant
            </div>
          </div>
        </div>

        <div className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full ${
          isDark ? "bg-neutral-800" : "bg-gray-100"
        }`}>
          <div className={`w-2 h-2 rounded-full ${getHealthColor()}`} />
          <span className={isDark ? "text-neutral-300" : "text-gray-600"}>
            {health?.status?.toUpperCase() || "CHECKING"}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className={`flex-1 overflow-y-auto overflow-x-hidden px-6 py-6 space-y-4 min-h-0 ${
        isDark ? "" : "bg-gray-50"
      }`}>
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 ${
              isDark ? "bg-neutral-800" : "bg-gray-200"
            }`}>
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-8 w-8 ${isDark ? "text-blue-400" : "text-blue-500"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className={`text-lg font-semibold mb-2 ${isDark ? "text-neutral-200" : "text-gray-800"}`}>
              Welcome to Data Dictionary
            </h3>
            <p className={`text-sm max-w-md ${isDark ? "text-neutral-400" : "text-gray-500"}`}>
              Ask questions about your database schema, generate SQL queries, or explore documentation.
            </p>
            <div className={`mt-6 grid grid-cols-2 gap-3 text-xs ${isDark ? "text-neutral-400" : "text-gray-500"}`}>
              <div className={`px-4 py-2 rounded-lg ${isDark ? "bg-neutral-800" : "bg-white border border-gray-200"}`}>
                💡 "Show total revenue"
              </div>
              <div className={`px-4 py-2 rounded-lg ${isDark ? "bg-neutral-800" : "bg-white border border-gray-200"}`}>
                📊 "Monthly trends"
              </div>
              <div className={`px-4 py-2 rounded-lg ${isDark ? "bg-neutral-800" : "bg-white border border-gray-200"}`}>
                📖 "Describe customers table"
              </div>
              <div className={`px-4 py-2 rounded-lg ${isDark ? "bg-neutral-800" : "bg-white border border-gray-200"}`}>
                🔍 "Top 10 sellers"
              </div>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} isDark={isDark} />
        ))}

        {loading && <Loader isDark={isDark} />}
        
        {/* Invisible element to scroll to */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className={`border-t py-4 flex-shrink-0 ${
        isDark ? "border-neutral-800 bg-neutral-900" : "border-gray-200 bg-white"
      }`}>
        <div className="max-w-3xl mx-auto px-4">
          <InputBox onSend={sendMessage} isDark={isDark} />
        </div>
      </div>
    </div>
  );
}
