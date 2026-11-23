import React, { useEffect, useRef, useState } from 'react';
import useAvailability from './useAvailability';

const API_URL = import.meta.env.VITE_API_URL;
const projects = [
  ['Mimi Bot', 'Mon assistant RAG', 'Comment fonctionne Mimi Bot ?'],
  ['Stage OCR', 'Extraction documentaire · AWS Bedrock', 'Peux-tu me parler du stage OCR de Noémie ?'],
  ['Onirique', 'Un jeu narratif porté par l’IA', 'Peux-tu me présenter le projet Onirique ?'],
  ['Mes passions', 'IA, jeux vidéo & création narrative', 'Qu’est-ce qui anime Noémie ?'],
];
const suggestions = [
  ['Découvrir ses projets', 'Quels sont les projets de Noémie ?', 'Ses projets ↗'],
  ['Son parcours en IA', 'Quel est le parcours de Noémie en intelligence artificielle ?', 'Son parcours en IA ↗'],
  ['Pourquoi Mimi ?', 'Pourquoi Noémie a-t-elle créé Mimi ?'],
];
const statusLabels = { checking: 'Vérification…', available: 'Disponible', unavailable: 'Indisponible' };

function Avatar({ className = '' }) {
  return <img src="/mimi-avatar.png" alt="Mimi" className={`avatar ${className}`} />;
}

function ChatHeader({ availability }) {
  return (
    <header className="chat-header">
      <Avatar />
      <div className="chat-identity"><h2>MimiBot</h2><p>L’assistante de Noémie</p></div>
      <p className={`availability ${availability}`} role="status" aria-live="polite">
        <span aria-hidden="true" />{statusLabels[availability]}
      </p>
    </header>
  );
}

function Portfolio({ onExplore }) {
  return (
    <aside id="portfolio" className="portfolio" aria-label="Le portfolio de Noémie">
      <p className="eyebrow"><span className="desktop-copy">Le portfolio de Noémie</span><span className="mobile-copy">Derrière Mimi, il y a…</span></p>
      <h1>Noémie</h1>
      <p className="profession">Développeuse en<br />intelligence artificielle</p>
      <p className="location">Toulouse, France</p>
      <section className="skills-section">
        <h2 className="eyebrow">Mes terrains de jeu</h2>
        <ul className="skills">{['Python', 'NLP', 'LLM', 'RAG', 'IA générative'].map(skill => <li key={skill}>{skill}</li>)}</ul>
      </section>
      <section className="education">
        <h2 className="eyebrow">En apprentissage, toujours</h2>
        <p>Simplon · Intelligence artificielle</p>
        <p className="muted">Et ensuite ? Une poursuite envisagée au CNAM.</p>
      </section>
      <section className="explore">
        <h2>Explorer avec Mimi</h2>
        <ol>{projects.map(([title, description, question], index) => (
          <li key={title}><button type="button" onClick={() => onExplore(question)}>
            <span className="project-number">0{index + 1}</span>
            <span className="project-copy"><span className="project-title">{title}</span><span className="muted">{description}</span></span>
          </button></li>
        ))}</ol>
      </section>
      <nav className="social-links" aria-label="Retrouver Noémie">
        <a href="https://github.com/NoemIADev" target="_blank" rel="noopener noreferrer">GitHub ↗</a>
        <a href="https://www.linkedin.com/in/noemie-majerus-devia" target="_blank" rel="noopener noreferrer">LinkedIn ↗</a>
      </nav>
      <section className="privacy">
        <h2>Un petit mot avant de discuter</h2>
        <p>Mimi est un projet personnel d’apprentissage, non professionnel. Ne communiquez aucune information personnelle ou confidentielle. Les questions sont enregistrées en base, sans identification nominative, uniquement pour améliorer le projet.</p>
      </section>
    </aside>
  );
}

function renderTextWithLinks(text) {
  return text.split(/(https?:\/\/[^\s]+|www\.[^\s]+)/g).map((part, index) => (
    /^(https?:\/\/|www\.)/.test(part)
      ? <a key={index} href={part.startsWith('http') ? part : `https://${part}`} target="_blank" rel="noopener noreferrer">{part}</a>
      : <React.Fragment key={index}>{part}</React.Fragment>
  ));
}

function ChatMessage({ role, text, welcome = false }) {
  return (
    <article className={`message ${role}`}>
      {role === 'bot' && <Avatar />}
      <div className="message-content">
        <p className="message-author">{role === 'bot' ? 'Mimi' : 'Toi'}</p>
        <div className="message-bubble">
          {welcome && <h3>Moi, c’est Mimi.</h3>}
          {welcome ? <>
            <p className="desktop-copy">{text}</p>
            <p className="mobile-copy">Le petit lien entre toi et l’univers de Noémie. Ses projets, son parcours, ses passions… Par quoi commence-t-on ?</p>
          </> : <p>{renderTextWithLinks(text)}</p>}
        </div>
      </div>
    </article>
  );
}

export default function App() {
  const availability = useAvailability(API_URL);
  const [view, setView] = useState('conversation');
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const sending = useRef(false);
  const request = useRef(null);
  const thread = useRef(null);
  const inputRef = useRef(null);
  const canSend = availability === 'available' && !isTyping && Boolean(sessionId);

  useEffect(() => {
    let id;
    try {
      id = localStorage.getItem('mimi_session_id') || crypto.randomUUID();
      localStorage.setItem('mimi_session_id', id);
    } catch {
      id = crypto.randomUUID();
    }
    setSessionId(id);
    return () => request.current?.abort();
  }, []);

  useEffect(() => {
    if (thread.current && (chatMessages.length || isTyping)) {
      thread.current.scrollTop = thread.current.scrollHeight;
    }
  }, [chatMessages, isTyping, view]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
    }
  }, [input, view]);

  async function handleSend(event) {
    event.preventDefault();
    const message = input.trim();
    if (!message || !canSend || sending.current) return;
    sending.current = true;
    setInput('');
    setChatMessages(previous => [...previous, { id: crypto.randomUUID(), role: 'user', text: message }]);
    setIsTyping(true);
    request.current = new AbortController();
    const timeout = window.setTimeout(() => request.current?.abort(), 120000);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: message, session_id: sessionId }),
        signal: request.current.signal,
      });
      if (!response.ok) throw new Error('Request failed');
      const data = await response.json();
      if (typeof data.response !== 'string' || !data.response.trim()) throw new Error('Empty response');
      setChatMessages(previous => [...previous, { id: crypto.randomUUID(), role: 'bot', text: data.response }]);
    } catch {
      setChatMessages(previous => [...previous, {
        id: crypto.randomUUID(), role: 'bot',
        text: 'Désolée, je n’ai pas pu répondre pour le moment. Tu peux réessayer dans un instant.',
      }]);
      setInput(previous => previous || message);
    } finally {
      window.clearTimeout(timeout);
      sending.current = false;
      setIsTyping(false);
    }
  }

  function explore(question) {
    setView('conversation');
    setInput(question);
    window.requestAnimationFrame(() => inputRef.current?.focus());
  }

  return (
    <main className={`app-shell view-${view}`}>
      <div className="mobile-header">
        {view === 'conversation' ? <ChatHeader availability={availability} /> : <p className="portfolio-heading">Le portfolio</p>}
      </div>
      <nav className="mobile-nav" aria-label="Navigation principale">
        <button type="button" aria-pressed={view === 'conversation'} aria-controls="conversation" onClick={() => setView('conversation')}>Conversation</button>
        <button type="button" aria-pressed={view === 'portfolio'} aria-controls="portfolio" onClick={() => setView('portfolio')}>Le portfolio</button>
      </nav>
      <Portfolio onExplore={explore} />
      <section id="conversation" className="conversation" aria-label="Conversation avec Mimi">
        <div className="desktop-header"><ChatHeader availability={availability} /></div>
        <div className="thread" ref={thread}>
          <p className="conversation-marker">Aujourd’hui<span className="desktop-copy"> · Une rencontre, quelques questions</span></p>
          <ChatMessage role="bot" welcome text={'Le petit lien entre toi et l’univers de Noémie.\nJe te raconte ses projets, son parcours et ce qui l’anime.\nPar quoi as-tu envie de commencer ?'} />
          <div className="suggestions">
            <p>Un peu d’inspiration ?</p>
            <div>{suggestions.map(([label, question, mobileLabel]) => <button type="button" key={label} className={mobileLabel ? '' : 'desktop-copy'} onClick={() => explore(question)}>
              <span className="desktop-copy">{label}</span>{mobileLabel && <span className="mobile-copy">{mobileLabel}</span>}
            </button>)}</div>
          </div>
          <div className="messages" role="log" aria-label="Messages" aria-live="polite" aria-relevant="additions">
            {chatMessages.map(message => <ChatMessage key={message.id} {...message} />)}
          </div>
          {isTyping && <div className="typing" role="status"><Avatar /><p>Mimi réfléchit<span aria-hidden="true">…</span></p></div>}
        </div>
        <footer className="composer">
          {availability === 'unavailable' && <p className="connection-notice" role="status">Mimi est momentanément indisponible. Tu peux toujours explorer le portfolio.</p>}
          <form onSubmit={handleSend} className="message-form">
            <textarea ref={inputRef} aria-label="Ton message à Mimi" rows={1} value={input}
              placeholder="Une question pour Mimi ?" onChange={event => setInput(event.target.value)}
              onKeyDown={event => {
                if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault();
                  if (canSend) event.currentTarget.form.requestSubmit();
                }
              }} />
            <button type="submit" disabled={!canSend || !input.trim()} aria-label="Envoyer le message">↑</button>
          </form>
          <p className="keyboard-help">Entrée pour envoyer · Maj + Entrée pour aller à la ligne</p>
          <p className="composer-note"><span className="mobile-copy">Pas d’informations personnelles ou confidentielles. </span>Mimi peut se tromper.<span className="desktop-copy"> Garde un regard curieux et critique.</span></p>
        </footer>
      </section>
    </main>
  );
}
