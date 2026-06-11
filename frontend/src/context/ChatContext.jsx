/* eslint-disable react-refresh/only-export-components */

import { createContext, useContext } from "react";
import useChats from "../hooks/useChats";

const ChatContext = createContext();

export function ChatProvider({ children }) {
  const chat = useChats();
  return (
    <ChatContext.Provider value={chat}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  return useContext(ChatContext);
}
