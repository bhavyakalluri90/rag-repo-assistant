import { useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";

type RagResponse = {
  answer: string;
  sources: string[];
};

function formatImplementationResponse(data: any) {
  if (!data.success) {
    return `
  ## Implementation Failed

  **Error:** ${data.error || "Unknown error"}

  ### Raw Response

  \`\`\`
  ${data.rawResponse || "No raw response available"}
  \`\`\`
  `;
    }

    const implementation = data.implementation;

    const files = implementation.filesToModify || [];
    const testPlan = implementation.testPlan || [];
    const risks = implementation.risks || [];

    return `
    # Jira Implementation Proposal

    ## Summary

    ${implementation.summary || "No summary provided."}

    ## Files to Modify

    ${
      files.length
        ? files
            .map(
              (file: any, index: number) => `
    ### ${index + 1}. \`${file.path}\`

    **Change Type:** ${file.changeType || "modify"}

    **Why this file changes:**  
    ${file.reason || "No reason provided."}
    `
            )
            .join("\n")
        : "No files suggested."
    }

    ## Test Plan

    ${
      testPlan.length
        ? testPlan.map((item: string) => `- ${item}`).join("\n")
        : "- No test plan provided."
    }

    ## Risks / Unknowns

    ${
      risks.length
        ? risks.map((item: string) => `- ${item}`).join("\n")
        : "- No risks provided."
    }

    ${
      data.diff
        ? `
    ## Git Diff

    \`\`\`diff
    ${data.diff}
    \`\`\`
    `
        : ""
    }

    ${
      data.testResult
        ? `
    ## Test Result

    **Command:** \`${data.testResult.command}\`  
    **Exit Code:** ${data.testResult.exitCode}

    \`\`\`
    ${data.testResult.stdout || data.testResult.stderr || "No output"}
    \`\`\`
    `
        : ""
    }

    ${
      data.lintResult
        ? `
    ## Lint Result

    **Command:** \`${data.lintResult.command}\`  
    **Exit Code:** ${data.lintResult.exitCode}

    \`\`\`
    ${data.lintResult.stdout || data.lintResult.stderr || "No output"}
    \`\`\`
    `
        : ""
    }
    `;
}

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

  const implementJira = async () => {
  setLoading(true);
  setAnswer("");
  setSources([]);

  try {
    const response = await fetch("http://127.0.0.1:8000/implement", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        ticket: question,
        auto_apply: false
      })
    });

    const data = await response.json();

    setAnswer(formatImplementationResponse(data));
  } catch (error) {
    setAnswer("Something went wrong while implementing the Jira ticket.");
  } finally {
    setLoading(false);
  }
};

  return (
   <main className="app">
  <section className="shell">
    <aside className="sidebar">
      <h1>RAG Repo Assistant</h1>
      <p>Ask questions about your docs or codebase.</p>

      <div className="controls">
        <select value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="general">General Question</option>
          <option value="files">Find Relevant Files</option>
          <option value="jira">Jira Implementation Plan</option>
          <option value="tests">Test Plan</option>
          <option value="implement">Implement Jira</option>
        </select>

        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Example: Where is routing handled?"
          rows={8}
        />

        <button onClick={implementJira} disabled={loading || !question.trim()}>
          Implement Jira
        </button>

        <button onClick={askQuestion} disabled={loading || !question.trim()}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>
    </aside>

    <section className="content">
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
  </section>
</main>
  );
}

export default App;