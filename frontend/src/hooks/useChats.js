import { useState, useEffect } from "react";
import { sendMessageToAPI } from "../services/api";

const STORAGE_KEY = "jarvis_chats";
const ACTIVE_CHAT_KEY = "jarvis_active_chat";

export default function useChats() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [loading, setLoading] = useState(false);

  // ✅ Load from storage
  useEffect(() => {
    const storedChats = localStorage.getItem(STORAGE_KEY);
    const storedActive = localStorage.getItem(ACTIVE_CHAT_KEY);

    if (storedChats) {
      const parsed = JSON.parse(storedChats);
      setChats(parsed);

      if (storedActive) {
        setActiveChatId(Number(storedActive));
      } else {
        setActiveChatId(parsed[0]?.id || null);
      }
    } else {
      createNewChat();
    }
  }, []);

  // ✅ Persist chats
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
  }, [chats]);

  // ✅ Persist active chat
  useEffect(() => {
    if (activeChatId) {
      localStorage.setItem(ACTIVE_CHAT_KEY, activeChatId);
    }
  }, [activeChatId]);

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
        mode: response.mode,
        sql: response.sql || null,
        explanation: response.explanation || null,
        result: response.result || null,
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
        text: error.message,
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
