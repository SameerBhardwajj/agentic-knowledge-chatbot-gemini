
import { useEffect, useState } from "react";

const API = "http://localhost:8000";
const headers = (id) => ({ "Content-Type": "application/json", "X-User-ID": String(id) });

export default function App() {
  const [users, setUsers] = useState([]);
  const [userId, setUserId] = useState("");
  const [chats, setChats] = useState([]);
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sources, setSources] = useState([]);
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/api/users`).then(r => r.json()).then(data => {
      setUsers(data);
      if (data.length) setUserId(String(data[0].id));
    }).catch(() => setError("Could not load users."));
  }, []);

  useEffect(() => {
    if (!userId) return;
    setChatId(null); setMessages([]); setSources([]); setTools([]);
    loadChats();
  }, [userId]);

  async function loadChats() {
    const r = await fetch(`${API}/api/chats`, { headers: headers(userId) });
    setChats(await r.json());
  }

  async function newChat() {
    const r = await fetch(`${API}/api/chats`, {
      method: "POST", headers: headers(userId),
      body: JSON.stringify({ title: "New chat" })
    });
    const chat = await r.json();
    setChats(c => [chat, ...c]); setChatId(chat.id);
    setMessages([]); setSources([]); setTools([]);
  }

  async function openChat(id) {
    const r = await fetch(`${API}/api/chats/${id}/messages`, { headers: headers(userId) });
    setChatId(id); setMessages(await r.json()); setSources([]); setTools([]);
  }

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setLoading(true); setError("");

    try {
      let id = chatId;
      if (!id) {
        const r = await fetch(`${API}/api/chats`, {
          method: "POST", headers: headers(userId),
          body: JSON.stringify({ title: text.slice(0, 60) })
        });
        const chat = await r.json();
        id = chat.id; setChatId(id); setChats(c => [chat, ...c]);
      }

      setMessages(m => [...m, { role: "user", content: text, created_at: new Date().toISOString() }]);
      setInput("");

      const r = await fetch(`${API}/api/chats/${id}/messages`, {
        method: "POST", headers: headers(userId),
        body: JSON.stringify({ message: text })
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Request failed.");

      setMessages(m => [...m, { role: "assistant", content: data.answer, created_at: new Date().toISOString() }]);
      setSources(data.sources || []);
      setTools(data.tools_used || []);
      await loadChats();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return <div className="app">
    <aside className="sidebar">
      <div className="eyebrow">PROJECT 2</div>
      <h1>Knowledge Agent</h1>
      <p className="muted">Gemini + RAG + PostgreSQL + Tool Calling</p>

      <label>Current demo user</label>
      <select value={userId} onChange={e => setUserId(e.target.value)}>
        {users.map(u => <option key={u.id} value={u.id}>{u.name} (ID {u.id})</option>)}
      </select>

      <button onClick={newChat}>+ New chat</button>
      <h3>Chat history</h3>
      <div className="history">
        {chats.map(c => <button className={c.id === chatId ? "history active" : "history"} key={c.id} onClick={() => openChat(c.id)}>{c.title}</button>)}
        {!chats.length && <span className="muted">No chats yet.</span>}
      </div>

      <div className="security">Demo identity uses <code>X-User-ID</code>. Replace with JWT/session auth in production.</div>
    </aside>

    <main className="main">
      <header className="topbar">
        <div><strong>Company Knowledge Assistant</strong><div className="muted">Company answers are restricted to retrieved knowledge.</div></div>
        {tools.length > 0 && <span className="badge">Tool: {tools.join(", ")}</span>}
      </header>

      <section className="messages">
        {!messages.length && <div className="empty"><h2>Ask the knowledge agent</h2><p>Try “How many annual leave days do I get?” or “What is my email address?”</p></div>}
        {messages.map((m, i) => <div key={i} className={`row ${m.role}`}><div className="bubble"><div className="role">{m.role === "user" ? "You" : "Agent"}</div>{m.content}</div></div>)}
        {loading && <div className="row assistant"><div className="bubble">Retrieving knowledge and checking tools…</div></div>}
      </section>

      <section className="sources">
        <strong>Retrieved knowledge</strong>
        {sources.length ? sources.map(s => <span className="source" key={s.id}>{s.title} · {s.similarity}</span>) : <span className="muted"> None for the last request.</span>}
      </section>

      {error && <div className="error">{error}</div>}

      <form className="composer" onSubmit={send}>
        <textarea value={input} onChange={e => setInput(e.target.value)} placeholder="Ask a question..." rows="3" disabled={loading}/>
        <button disabled={loading || !input.trim()}>{loading ? "Working…" : "Send"}</button>
      </form>
    </main>
  </div>;
}
