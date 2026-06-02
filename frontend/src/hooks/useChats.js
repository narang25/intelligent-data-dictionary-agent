import { useState, useEffect } from "react";
import { sendMessageToAPI } from "../services/api";

const STORAGE_KEY = "jarvis_chats";
const ACTIVE_CHAT_KEY = "jarvis_active_chat";

// Generate a short title from the first message
const generateTitle = (text) => {
  if (!text) return "New Chat";
  
  // Clean and truncate the text
  const cleaned = text.trim().replace(/\s+/g, ' ');
  
  // Take first 30 characters, try to break at word boundary
  if (cleaned.length <= 30) return cleaned;
  
  const truncated = cleaned.substring(0, 30);
  const lastSpace = truncated.lastIndexOf(' ');
  
  if (lastSpace > 15) {
    return truncated.substring(0, lastSpace) + '...';
  }
  
  return truncated + '...';
};

export default function useChats() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // ✅ Load from storage and ensure a chat exists
  useEffect(() => {
    const storedChats = localStorage.getItem(STORAGE_KEY);
    const storedActive = localStorage.getItem(ACTIVE_CHAT_KEY);

    if (storedChats) {
      try {
        const parsed = JSON.parse(storedChats);
      
        if (!Array.isArray(parsed) || parsed.length === 0) {
          // No chats exist, create a new one
          const newChat = {
            id: Date.now(),
            title: "New Chat",
            sessionId: null,
            messages: [],
            isRenamed: false,
          };
          setChats([newChat]);
          setActiveChatId(newChat.id);
        } else {
          setChats(parsed);
          
          // Check if there's an empty "New Chat" we can reuse
          const emptyChat = parsed.find(
            (c) => c.messages.length === 0 && c.title === "New Chat"
          );
          
          if (emptyChat) {
            // Reuse existing empty chat
            setActiveChatId(emptyChat.id);
          } else if (storedActive && parsed.find(c => c.id === Number(storedActive))) {
            // Use stored active chat if it still exists
            setActiveChatId(Number(storedActive));
          } else {
            // Create a new chat for fresh start
            const newChat = {
              id: Date.now(),
              title: "New Chat",
              sessionId: null,
              messages: [],
              isRenamed: false,
            };
            setChats([newChat, ...parsed]);
            setActiveChatId(newChat.id);
          }
        }
      } catch (e) {
        console.error("Failed to parse stored chats:", e);
        // Create fresh chat on parse error
        const newChat = {
          id: Date.now(),
          title: "New Chat",
          sessionId: null,
          messages: [],
          isRenamed: false,
        };
        setChats([newChat]);
        setActiveChatId(newChat.id);
      }
    } else {
      // No stored chats, create first chat
      const newChat = {
        id: Date.now(),
        title: "New Chat",
        sessionId: null,
        messages: [],
        isRenamed: false,
      };
      setChats([newChat]);
      setActiveChatId(newChat.id);
    }
    
    // Mark as initialized after loading
    setIsInitialized(true);
  }, []);

  // ✅ Persist chats (only after initialization)
  useEffect(() => {
    if (isInitialized && chats.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
    }
  }, [chats, isInitialized]);

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
      isRenamed: false,  // Track if user manually renamed
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

    // Auto-generate title from first message if not manually renamed
    const isFirstMessage = activeChat.messages.length === 0;
    if (isFirstMessage && !activeChat.isRenamed) {
      const autoTitle = generateTitle(text);
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === activeChatId
            ? { ...chat, title: autoTitle }
            : chat
        )
      );
    }

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
        confidence: response.confidence || null,
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
  const renameChat = (chatId, newTitle) => {
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === chatId
          ? { ...chat, title: newTitle, isRenamed: true }
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
    renameChat,
    loading,
  };
}
