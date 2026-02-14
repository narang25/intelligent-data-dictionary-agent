import { useState } from "react";

export default function InputBox({ onSend }) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  return (
    <div className="flex items-center gap-3 bg-neutral-800 rounded-full px-4 py-3">
      
      {/* Plus Button */}
      <button className="text-neutral-400 hover:text-white transition text-xl">
        +
      </button>

      {/* Input */}
      <input
        type="text"
        placeholder="Ask anything..."
        className="flex-1 bg-transparent text-neutral-200 text-sm focus:outline-none"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
      />

      {/* Circular Send Button */}
      <button
        onClick={handleSend}
        className="w-9 h-9 flex items-center justify-center rounded-full bg-blue-600 hover:bg-blue-700 transition"
      >
        <span className="text-white text-lg leading-none">↑</span>
      </button>
    </div>
  );
}
