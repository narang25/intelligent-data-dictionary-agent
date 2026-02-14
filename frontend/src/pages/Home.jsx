import Sidebar from "../components/Sidebar/Sidebar";
import ChatWindow from "../components/Chat/ChatWindow";
import useChats from "../hooks/useChats";

export default function Home() {
  const {
    chats,
    activeChat,
    activeChatId,
    setActiveChatId,
    createNewChat,
    sendMessage
  } = useChats();

  return (
    <div className="h-screen flex bg-neutral-900">

      {/* Sidebar */}
      <div className="w-64 flex-shrink-0">
        <Sidebar
          chats={chats}
          activeChatId={activeChatId}
          setActiveChatId={setActiveChatId}
          createNewChat={createNewChat}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {activeChat && (
          <ChatWindow
            messages={activeChat.messages}
            sendMessage={sendMessage}
          />
        )}
      </div>
    </div>
  );
}
