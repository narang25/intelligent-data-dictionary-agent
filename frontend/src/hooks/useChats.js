import { useState, useEffect } from "react";
import { sendMessageToAPI } from "../services/api";

const STORAGE_KEY = "jarvis_chats";

export default function useChats() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      setChats(parsed);
      setActiveChatId(parsed[0]?.id || null);
    } else {
      createNewChat();
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
  }, [chats]);

  const activeChat = chats.find((c) => c.id === activeChatId);

  const createNewChat = () => {
    const newChat = {
      id: Date.now(),
      title: "New Chat",
      sessionId: null,
      messages: [],
    };

    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(newChat.id);
  };

  const sendMessage = async (text) => {
    if (!activeChat) return;

    const userMessage = {
      id: Date.now(),
      sender: "user",
      text,
    };

    updateMessages([...activeChat.messages, userMessage]);
    setLoading(true);

    try {
      const response = await sendMessageToAPI(
        text,
        activeChat.sessionId
      );

      const assistantMessage = {
        id: Date.now() + 1,
        sender: "assistant",
        text: response.answer,
      };

      updateMessages([
        ...activeChat.messages,
        userMessage,
        assistantMessage,
      ]);

      updateSessionId(response.session_id);

    } catch (error) {
      const errorMessage = {
        id: Date.now() + 2,
        sender: "assistant",
        text: "Error: Failed to fetch response from server.",
      };

      updateMessages([
        ...activeChat.messages,
        userMessage,
        errorMessage,
      ]);
    }

    setLoading(false);
  };

  const updateMessages = (messages) => {
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === activeChatId ? { ...chat, messages } : chat
      )
    );
  };

  const updateSessionId = (sessionId) => {
    if (!sessionId) return;

    setChats((prev) =>
      prev.map((chat) =>
        chat.id === activeChatId
          ? { ...chat, sessionId }
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
    sendMessage,
    loading,
  };
}
