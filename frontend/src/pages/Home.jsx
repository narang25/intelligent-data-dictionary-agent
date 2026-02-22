import Sidebar from "../components/Sidebar/Sidebar";
import ChatWindow from "../components/Chat/ChatWindow";
import { useChat } from "../context/ChatContext"; // ✅ changed
import useHealth from "../hooks/useHealth";

export default function Home() {
  const {
    chats,
    activeChat,
    activeChatId,
    setActiveChatId,
    createNewChat,
    sendMessage,
    renameChat,
    loading,
  } = useChat(); // ✅ changed

  const health = useHealth();

  return (
    <div className="flex h-screen w-full">
      <div className="w-[200px] min-w-[200px] max-w-[200px] flex-shrink-0">
       <Sidebar
  chats={chats}
  activeChatId={activeChatId}
  setActiveChatId={setActiveChatId}
  createNewChat={createNewChat}
  renameChat={renameChat}
/>

      </div>

      <ChatWindow
        messages={activeChat?.messages || []}
        sendMessage={sendMessage}
        loading={loading}
        health={health}
      />
    </div>
  );
}
