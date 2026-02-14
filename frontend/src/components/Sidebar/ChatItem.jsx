export default function ChatItem({ chat, isActive, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`p-2 rounded-md cursor-pointer text-sm truncate transition ${
        isActive
          ? "bg-neutral-800"
          : "hover:bg-neutral-800"
      }`}
    >
      {chat.title}
    </div>
  );
}
