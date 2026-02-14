export default function Button({ children, onClick }) {
  return (
    <button
      onClick={onClick}
      className="bg-blue-500 text-white px-4 rounded-lg text-sm hover:bg-blue-600 transition"
    >
      {children}
    </button>
  );
}
