export default function MessageBubble({ message }) {
  const isUser = message.sender === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`px-4 py-3 rounded-xl max-w-[85%] text-sm whitespace-pre-wrap ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-neutral-800 text-neutral-200"
        }`}
      >
        {/* Mode Badge */}
        {!isUser && message.mode && (
          <div className="text-xs mb-2 opacity-60 uppercase">
            {message.mode}
          </div>
        )}

        {/* Main Text */}
        <div>{message.text}</div>

        {/* SQL Section */}
        {!isUser && message.mode === "sql" && message.sql && (
          <div className="mt-4 space-y-3">

            <div className="bg-black text-green-400 p-3 rounded-lg text-xs overflow-x-auto">
              <div className="text-white mb-1 font-semibold">
                SQL Query
              </div>
              <pre>{message.sql}</pre>
            </div>

            {message.explanation && (
              <div className="bg-neutral-700 p-3 rounded-lg text-xs">
                <div className="font-semibold mb-1">
                  Explanation
                </div>
                {message.explanation}
              </div>
            )}

            {message.result?.columns && (
              <div className="overflow-x-auto">
                <div className="text-xs font-semibold mb-2">
                  Query Result
                </div>

                <table className="text-xs border border-neutral-700 w-full">
                  <thead>
                    <tr className="bg-neutral-900">
                      {message.result.columns.map((col, idx) => (
                        <th
                          key={idx}
                          className="border border-neutral-700 px-3 py-2"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {message.result.rows.map((row, rIndex) => (
                      <tr key={rIndex}>
                        {row.map((cell, cIndex) => (
                          <td
                            key={cIndex}
                            className="border border-neutral-700 px-3 py-2"
                          >
                            {String(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>

              </div>
            )}

          </div>
        )}

      </div>
    </div>
  );
}
