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
    loading,
  } = useChat(); // ✅ changed

  const health = useHealth();

  return (
    <div className="flex h-screen">
      <div className="w-64">
        <Sidebar
          chats={chats}
          activeChatId={activeChatId}
          setActiveChatId={setActiveChatId}
          createNewChat={createNewChat}
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
