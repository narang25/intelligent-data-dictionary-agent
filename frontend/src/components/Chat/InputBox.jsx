import { useState } from "react";

export default function InputBox({ onSend, isDark = true }) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  return (
    <div className={`flex items-center gap-2 rounded-xl px-4 py-2 transition-colors ${
      isDark 
        ? "bg-neutral-800 border border-neutral-700" 
        : "bg-gray-100 border border-gray-300"
    }`}>
      <input
        type="text"
        placeholder="Ask anything..."
        className={`flex-1 bg-transparent text-sm focus:outline-none ${
          isDark 
            ? "text-neutral-200 placeholder-neutral-500" 
            : "text-gray-800 placeholder-gray-400"
        }`}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
      />
      <button
        onClick={handleSend}
        className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-500 transition-colors flex items-center gap-2"
      >
        <span>Send</span>
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  );
}
