import { useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";

type RagResponse = {
  answer: string;
  sources: string[];
};

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("general");

  const askQuestion = async () => {
    setLoading(true);
    setAnswer("");
    setSources([]);

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ question, mode })
      });

      const data: RagResponse = await response.json();

      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (error) {
      setAnswer("Something went wrong while asking the RAG assistant.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app">
      <section className="card">
        <h1>RAG Repo Assistant</h1>
        <p>Ask questions about your docs or codebase.</p>

       <div className="controls">
        <select value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="general">General Question</option>
          <option value="files">Find Relevant Files</option>
          <option value="jira">Jira Implementation Plan</option>
          <option value="tests">Test Plan</option>
        </select>

        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Example: Where is payment handled?"
          rows={5}
        />

        <button onClick={askQuestion} disabled={loading || !question.trim()}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

       {answer && (
        <section className="answer">
          <h2>Answer</h2>
          <div className="markdown-answer">
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div>
        </section>
      )}

        {sources.length > 0 && (
          <section className="sources">
            <h2>Sources</h2>
            <ul>
              {sources.map((source) => (
                <li key={source}>{source}</li>
              ))}
            </ul>
          </section>
        )}
      </section>
    </main>
  );
}

export default App;