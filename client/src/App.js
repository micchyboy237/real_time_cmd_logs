import React, { useState } from "react";
import { usePreferredTheme } from "./usePreferredTheme";

const DEFAULT_COMMAND = "ls -la .";

function App() {
  const [theme, setTheme] = usePreferredTheme();
  const [command, setCommand] = useState(DEFAULT_COMMAND);
  const [logs, setLogs] = useState([]);

  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const handleExecute = () => {
    if (!command) {
      alert("Please enter a command.");
      return;
    }

    const eventSource = new EventSource(
      `http://localhost:3001/stream?command=${encodeURIComponent(command)}`
    );

    eventSource.onmessage = (event) => {
      setLogs((prevLogs) => [...prevLogs, event.data]);
    };

    eventSource.onerror = () => {
      setLogs((prevLogs) => [
        ...prevLogs,
        "Error connecting to the server. Please try again.",
      ]);
      eventSource.close();
    };
  };

  return (
    <div
      className={
        theme === "dark"
          ? "dark bg-gray-900 text-white"
          : "bg-gray-100 text-gray-900"
      }
    >
      <div className="min-h-screen flex flex-col items-center justify-center">
        <header className="mb-8">
          <h1 className="text-3xl font-bold">Real-Time Command Viewer</h1>
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="mt-4 px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-700 
            bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700"
          >
            Toggle {theme === "dark" ? "Light" : "Dark"} Mode
          </button>
        </header>

        <div className="w-full max-w-md">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Enter command"
            className="w-full p-3 border border-gray-300 rounded-md dark:border-gray-700 dark:bg-gray-800 
            focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleExecute}
            className="w-full mt-3 px-4 py-2 bg-blue-500 text-white font-medium rounded-md hover:bg-blue-600"
          >
            Execute
          </button>
        </div>

        <div className="w-full max-w-lg mt-6">
          <h2 className="text-xl font-semibold">Logs</h2>
          <div
            className="h-40 overflow-y-auto mt-2 p-3 border border-gray-300 dark:border-gray-700 
            rounded-md bg-gray-50 dark:bg-gray-900"
          >
            {logs.length === 0 ? (
              <p>No logs available yet.</p>
            ) : (
              logs.map((log, index) => (
                <p key={index} className="whitespace-pre-wrap mb-1">
                  {log}
                </p>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
