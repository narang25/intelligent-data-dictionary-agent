import { useState } from "react";

export default function useChats() {
  const [chats, setChats] = useState([
    {
      id: 1,
      title: "New Chat",
      messages: [
        { id: 1, text: "Hello 👋", sender: "bot" }
      ]
    }
  ]);

  const [activeChatId, setActiveChatId] = useState(1);

  const activeChat = chats.find(chat => chat.id === activeChatId);

  const createNewChat = () => {
    const newChat = {
      id: Date.now(),
      title: "New Chat",
      messages: []
    };

    setChats(prev => [newChat, ...prev]);
    setActiveChatId(newChat.id);
  };

  const sendMessage = (text) => {
    if (!text.trim()) return;

    setChats(prev =>
      prev.map(chat =>
        chat.id === activeChatId
          ? {
              ...chat,
              messages: [
                ...chat.messages,
                { id: Date.now(), text, sender: "user" },
                {
                  id: Date.now() + 1,
                  text: "Mock response...",
                  sender: "bot"
                }
              ]
            }
          : chat
      )
    );
  };

  return {
    chats,
    activeChat,
    activeChatId,
    setActiveChatId,
    createNewChat,
    sendMessage
  };
}
