import React, { useEffect, useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL;
console.log("API_URL =", API_URL);

const introCards = [
  {
    title: 'Parcours',
    description:
      'Reconversion vers le développement en intelligence artificielle, avec une approche polyvalente combinant data, algorithmie et création d’applications orientées utilisateur.'
  },
  {
    title: 'Compétences',
    description:
      'Python, LLM apps, structuration RAG, prompt engineering et bien d’autres, demandez moi !'
  },
  {
    title: 'Projets',
    description:
      'Projet personnel (Onirique, en conception) et projets réalisés en formation autour de l’IA, combinant machine learning, développement d’algorithmes et création d’applications et agents conversationnels.'
  }
];



function BrowserFrame({ children }) {
  return (
      
      <div className="p-8 lg:p-10">{children}</div>
    
  );
}

function InfoCard({ title, description }) {
  return (
    <article className="rounded-2xl border border-slate-200/70 bg-white/75 p-5 shadow-panel transition hover:-translate-y-0.5 hover:shadow-md">
      <h3 className="text-lg font-semibold text-navy">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-slateblue">{description}</p>
    </article>
  );
}

function LeftIntroPanel() {
  return (
    <section className="rounded-[30px] border border-slate-200/80 bg-paper px-8 py-10 lg:px-12">
      <p className="text-6xl font-semibold tracking-tight text-navy">Mimi</p>
      <h2 className="mt-2 text-3xl font-medium text-slateblue">L’assistante de Noémie</h2>

      <div className="my-8 border-t border-slate-300/70" />

      <p className="max-w-2xl text-lg leading-relaxed text-slateblue">
        “Bonjour, je suis Mimi, l’assistante de Noémie. Je suis là pour vous aider à découvrir son parcours, ses compétences et ses projets. Vous pouvez me poser toutes les questions que vous voulez sur elle, et je ferai de mon mieux pour vous répondre.”
      </p>

      <div className="mt-8 grid gap-4">
        {introCards.map((card) => (
          <InfoCard key={card.title} {...card} />
        ))}
      </div>
    </section>
  );
}

function renderTextWithLinks(text) {
  const urlRegex = /(https?:\/\/[^\s]+|www\.[^\s]+)/g;
  const parts = text.split(urlRegex);

  return parts.map((part, index) => {
    const isUrl = urlRegex.test(part);

    if (!isUrl) {
      return <React.Fragment key={index}>{part}</React.Fragment>;
    }

    const href = part.startsWith("http") ? part : `https://${part}`;

    return (
      <a
        key={index}
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="underline"
      >
        {part}
      </a>
    );
  });
}

function ChatMessage({ role, text, avatar }) {
  const isBot = role === 'bot';

  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'}`}>
      <div className={`flex max-w-[88%] items-end gap-3 ${isBot ? '' : 'flex-row-reverse'}`}>
        {isBot && (
          <img
            src={avatar}
            alt="Avatar de Mimi"
            className="h-24 w-24 shrink-0 rounded-full border border-slate-300/70 bg-slate-100 object-cover"
          />
        )}
        <div
          className={`rounded-2xl px-5 py-3 text-[15px] leading-relaxed shadow-sm ${
            isBot
              ? 'rounded-bl-md border border-blue-200/80 bg-bubble text-navy'
              : 'rounded-br-md bg-navy text-blue-50'
          }`}
        >
          {renderTextWithLinks(text)}
        </div>
      </div>
    </div>
  );
}

function ChatInput({ onSend }) {
  const [input, setInput] = React.useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  return (
    <form
      className="mt-5 flex items-center gap-3 border-t border-slate-200 pt-4"
      onSubmit={(e) => {
        e.preventDefault();
        handleSend();
      }}
    >
      <input
        type="text"
        placeholder="Écrivez votre message..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="h-12 flex-1 rounded-xl border border-slate-300 bg-white px-4"
      />

      <button type="submit" className="h-12 rounded-xl bg-navy px-5 text-white">
        Envoyer
      </button>
    </form>
  );
}

function ChatPanel({ chatMessages, isTyping, onSend }) {

  return (
    <section className="rounded-[30px] border border-blue-200/80 bg-paper p-6 shadow-panel lg:p-7">
      <header className="flex items-center justify-between border-b border-blue-100 pb-4">
        <div>
          <h3 className="text-2xl font-semibold text-navy">MimiBot</h3>
          <p className="mt-1 flex items-center gap-2 text-sm text-slateblue">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            En ligne
          </p>
        </div>
      </header>

      <div className="mt-5 h-[460px] space-y-4 overflow-y-auto pr-1">
        {chatMessages.map((message) => (
          <ChatMessage key={message.id} {...message} />
        ))}
        {isTyping && (
  <div className="flex gap-3 items-center">
    <img
      src="/mimi-avatar.png"
      className="h-14 w-14 rounded-full object-cover"
    />
    <div className="bg-slate-200 px-4 py-2 rounded-2xl flex gap-1">
      <span className="animate-bounce">.</span>
      <span className="animate-bounce delay-100">.</span>
      <span className="animate-bounce delay-200">.</span>
    </div>
  </div>
)}
      </div>

      <ChatInput onSend={onSend} />
    </section>
  );
}

export default function App() {
  const [isTyping, setIsTyping] = useState(false);

  const [sessionId, setSessionId] = useState("");

  const [chatMessages, setChatMessages] = useState([
    {
      id: 1,
      role: 'bot',
      avatar: '/mimi-avatar.png',
      text: 'Bonjour, je suis Mimi. Vous pouvez me demander qui est Noémie, sur quels projets elle travaille, ou quelles technologies elle utilise.'
    }
  ]);

  useEffect(() => {
  let storedSessionId = localStorage.getItem("mimi_session_id");

  if (!storedSessionId) {
    storedSessionId = crypto.randomUUID();
    localStorage.setItem("mimi_session_id", storedSessionId);
  }

  setSessionId(storedSessionId);
}, []);

  const handleSend = async (message) => {
    if (!sessionId) return;
    const userMessage = {
      id: Date.now(),
      role: 'user',
      text: message
    };

    setChatMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: message,
      session_id: sessionId,
    }),
  });

  const data = await res.json();

  const botMessage = {
    id: Date.now() + 1,
    role: 'bot',
    avatar: '/mimi-avatar.png',
    text: data.response
  };

  setChatMessages((prev) => [...prev, botMessage]);
} catch (err) {
  console.error(err);

  const errorMessage = {
    id: Date.now() + 1,
    role: 'bot',
    avatar: '/mimi-avatar.png',
    text: "Désolée, j'ai eu un souci pour répondre."
  };

  setChatMessages((prev) => [...prev, errorMessage]);
} finally {
  setIsTyping(false);
}
  };

  return (
    <main className="min-h-screen px-6 py-8 lg:px-10 lg:py-12">
      <BrowserFrame>
        <div className="relative grid gap-0 lg:grid-cols-2">
          <div className="pb-8 pr-0 lg:pb-0 lg:pr-8">
            <LeftIntroPanel />
          </div>

          <div className="lg:pl-8">
            <ChatPanel
              chatMessages={chatMessages}
              isTyping={isTyping}
              onSend={handleSend}
            />
          </div>

          <div className="pointer-events-none absolute left-1/2 top-0 hidden h-full w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-slate-300 to-transparent lg:block" />
        </div>
      </BrowserFrame>
    </main>
  );
}
