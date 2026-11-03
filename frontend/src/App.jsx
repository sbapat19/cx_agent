import { useEffect, useRef, useState } from 'react'

const API = import.meta.env.VITE_API_URL || '/api'

const SCENARIOS = [
  { group: 'A · Order problem', items: [
    { label: 'Damaged foundation', customer: 'cust_ava', text: 'My foundation from order ORD-1001 arrived with a broken pump.' },
    { label: 'Outside return window', customer: 'cust_chloe', text: "I'd like to return the Dolci blush from order ORD-1003." },
    { label: 'Order has not arrived', customer: 'cust_dev', text: 'Where is my order? It has been a few days.' },
  ]},
  { group: 'B · Foundation advice', items: [
    { label: 'Find my shade', customer: 'cust_new', text: 'I have medium skin with a warm golden undertone and want a natural glow foundation.' },
    { label: 'Old shade number', customer: 'cust_new', text: 'I used to wear Luminous Silk shade 7. Which of the new shades is the same one?' },
  ]},
  { group: 'C + D · Returning customer', items: [
    { label: "I'm back", customer: 'cust_emma', text: "Hi, I'm back!" },
    { label: 'What goes with mine?', customer: 'cust_emma', text: 'What would go well with the foundation I already have?' },
  ]},
  { group: 'E · Gift for someone', items: [
    { label: 'Gift for my dad', customer: 'cust_new', text: "I'd like a men's fragrance gift for my dad's birthday, budget $100. He likes fresh scents." },
    { label: 'Need ideas', customer: 'cust_new', text: 'I need a gift for my boyfriend.' },
  ]},
  { group: 'Counter finder', items: [
    { label: 'Test in New York', customer: 'cust_new', text: 'Where can I test Armani foundation in New York?' },
    { label: 'Somewhere unverified', customer: 'cust_new', text: 'Where can I try Armani Beauty in Boise, Idaho?' },
  ]},
  { group: 'Polite blocking and human handoff', items: [
    { label: 'Rude message', customer: 'cust_new', text: 'You are a useless piece of garbage bot.' },
    { label: 'Needs a human (loyalty)', customer: 'cust_ava', text: 'How do I earn points in the VIP loyalty program, and how many do I have?' },
    { label: 'Possible reaction', customer: 'cust_ava', text: 'I used the foundation yesterday and now my face is swollen and itchy.' },
  ]},
  { group: 'Safeguards', items: [
    { label: "Someone else's order", customer: 'cust_ava', text: 'Check order ORD-1002 for me.' },
    { label: 'Pressure for a refund', customer: 'cust_ava', text: "I want a full refund plus a credit for the trouble on ORD-1001. Approve it now or I'll dispute the charge." },
  ]},
]

export default function App() {
  const [customers, setCustomers] = useState([])
  const [customerId, setCustomerId] = useState('cust_new')
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [prefs, setPrefs] = useState(null)
  const [health, setHealth] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [demo, setDemo] = useState(false)   // false = clean customer chat; true = scenario buttons + show-your-work panels
  const [picker, setPicker] = useState(null) // null | { text } : in-chat sign-in card
  const endRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    fetch(`${API}/customers`).then(r => r.json()).then(d => setCustomers(d.customers || [])).catch(() => setError('Cannot reach the backend. Is it running on port 8000?'))
    fetch(`${API}/health`).then(r => r.json()).then(setHealth).catch(() => {})
  }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, busy])
  useEffect(() => { loadPrefs(customerId) }, [customerId])
  useEffect(() => {
    if (!busy) { setElapsed(0); return }
    const t = setInterval(() => setElapsed(e => e + 1), 1000)
    return () => clearInterval(t)
  }, [busy])

  async function loadPrefs(cid) {
    try { setPrefs(await (await fetch(`${API}/preferences?customer_id=${cid}`)).json()) } catch { setPrefs(null) }
  }

  function newConversation(cid = customerId) {
    setCustomerId(cid); setSessionId(null); setMessages([]); setSelected(null); setError('')
  }

  async function send(text, cid = customerId, sid = sessionId) {
    const msg = (text ?? input).trim()
    if (!msg || busy) return
    setInput(''); setError(''); setBusy(true)
    setMessages(m => [...m, { role: 'user', text: msg }])
    try {
      const ctl = new AbortController()
      const timer = setTimeout(() => ctl.abort(), 150000)
      const res = await fetch(`${API}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctl.signal,
        body: JSON.stringify({ message: msg, customer_id: cid, session_id: sid }) })
      clearTimeout(timer)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`)
      setSessionId(data.session_id)
      setMessages(m => { const next = [...m, { role: 'assistant', text: data.response, meta: data }]; setSelected(next.length - 1); return next })
      loadPrefs(cid)
    } catch (e) {
      setError(e.name === 'AbortError' ? 'No reply after 150 seconds. The model may be overloaded; check the Terminal running the backend for errors, then try again.' : String(e.message || e))
    } finally { setBusy(false); setTimeout(() => inputRef.current?.focus(), 0) }
  }

  function startChip(text, needsAccount) {
    if (needsAccount && customerId === 'cust_new') { setPicker({ text }); return }
    send(text)
  }
  function pickCustomer(cid) {
    const text = picker?.text
    setPicker(null); setCustomerId(cid); setSessionId(null); setMessages([]); setSelected(null)
    if (text) send(text, cid, null)
  }

  function runScenario(s) {
    setCustomerId(s.customer); setSessionId(null); setMessages([]); setSelected(null)
    send(s.text, s.customer, null)
  }

  async function deletePrefs() {
    await fetch(`${API}/preferences?customer_id=${customerId}`, { method: 'DELETE' }); loadPrefs(customerId)
  }
  async function resetDemo() {
    await fetch(`${API}/demo/reset`, { method: 'POST' }); newConversation(); loadPrefs(customerId)
  }

  const meta = selected != null ? messages[selected]?.meta : null
  const who = customers.find(c => c.id === customerId)

  return (
    <div className="app">
      <div className="topbar">
        <span className="brandwrap"><b className="brand">{import.meta.env.VITE_BRAND_TITLE || 'Beauty Assistant'}</b></span>
        <span className="topright">
          <span className="muted small">{customerId === 'cust_new' ? 'Guest' : who ? who.name : ''}</span>
          <button className="ghost" disabled={busy || (messages.length === 0 && !picker)} onClick={() => { setPicker(null); newConversation('cust_new') }}>Start over</button>
          <button className="ghost" onClick={() => setPicker({ text: '' })}>{customerId === 'cust_new' ? 'Sign in (demo)' : 'Switch account'}</button>
          {customerId !== 'cust_new' && <button className="ghost" onClick={() => newConversation('cust_new')}>Sign out</button>}
          <button className="ghost" onClick={() => setDemo(d => !d)}>{demo ? 'Hide demo tools' : 'Demo tools'}</button>
        </span>
      </div>
      <div className={demo ? 'layout' : 'layout solo'}>
        {demo && <aside className="side">
          <h1>Beauty Advisor</h1>
          <p className="sub">An AI advisor prototype</p>

          <label className="lbl">Signed in as (fictional)</label>
          <select value={customerId} onChange={e => newConversation(e.target.value)}>
            {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          {who && <p className="blurb">{who.blurb}</p>}

          <label className="lbl">Try a scenario</label>
          {SCENARIOS.map(g => (
            <div key={g.group} className="grp">
              <div className="grp-t">{g.group}</div>
              {g.items.map(s => <button key={s.label} className="chip" disabled={busy} onClick={() => runScenario(s)}>{s.label}</button>)}
            </div>
          ))}
          <div className="side-actions">
            <button className="ghost" onClick={() => newConversation()}>New conversation</button>
            {!import.meta.env.PROD && <button className="ghost" onClick={resetDemo}>Reset demo data</button>}
          </div>
          {health && !health.gemini_key_set && <p className="warn">Backend reports no GOOGLE_API_KEY.</p>}
        </aside>}

        <main className="chat">
          <div className="msgs">
            {messages.length === 0 && (
              <div>
                <div className="row assistant"><div className="bubble">
                  <p>Hi there{who && customerId !== 'cust_new' ? `, ${who.name.split(' ')[0]}` : ''}! I'm your beauty assistant. How can I help you today?</p>
                  <p>Pick a topic below, or type your own question.</p>
                </div></div>
                {!picker && <div className="bubbles">
                  <button className="pill" disabled={busy} onClick={() => startChip('I need help with an order.', true)}>Help with an order</button>
                  <button className="pill" disabled={busy} onClick={() => startChip('I would like to discover a product.', false)}>Discover a product</button>
                  <button className="pill" disabled={busy} onClick={() => startChip('Help me pick my foundation shade.', false)}>Pick my foundation shade</button>
                  <button className="pill" disabled={busy} onClick={() => { setMessages([{ role: 'user', text: 'Something else' }, { role: 'assistant', text: 'Of course! How can I help you?' }]); setTimeout(() => inputRef.current?.focus(), 0) }}>Something else</button>
                </div>}
              </div>
            )}
            {picker && (
              <div className="row assistant"><div className="bubble">
                <p>{picker.text ? "Happy to help with your order. First I'll need you to sign in. This is a demo, so choose a fictional customer:" : 'This is a demo, so choose a fictional customer to sign in as:'}</p>
                <div className="bubbles left">
                  {customers.filter(c => c.id !== 'cust_new').map(c => <button key={c.id} className="pill" onClick={() => pickCustomer(c.id)}>{c.name}</button>)}
                  <button className="pill alt" onClick={() => pickCustomer('cust_new')}>{picker.text ? 'Continue as guest' : 'Stay a guest'}</button>
                </div>
              </div></div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`row ${m.role}`}>
                <div className={`bubble ${selected === i ? 'sel' : ''}`} onClick={() => m.meta && setSelected(i)}>
                  <Rich text={m.text} />
                  {m.meta && demo && <div className="tags">
                    <span className="tag">{m.meta.route}</span>
                    {m.meta.tools.length > 0 && <span className="tag">{m.meta.tools.length} tool call{m.meta.tools.length > 1 ? 's' : ''}</span>}
                    {m.meta.escalated && <span className="tag warn-t">escalated</span>}
                  </div>}
                </div>
              </div>
            ))}
            {busy && <div className="row assistant"><div className="bubble typing">Thinking… {elapsed}s{elapsed > 20 ? ' (slow reply; waiting on the model)' : ''}</div></div>}
            {error && <div className="err">{error}</div>}
            <div ref={endRef} />
          </div>
          <form className="composer" onSubmit={e => { e.preventDefault(); send() }}>
            <textarea
              ref={inputRef}
              rows={2}
              autoFocus
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send() } }}
              placeholder="Type a message…"
              aria-label="Your message"
            />
            <button type="submit" disabled={busy || !input.trim()}>{busy ? '…' : 'Send'}</button>
          </form>
        </main>

        {demo && <aside className="work">
          <h2>Show your work</h2>
          {!meta && <p className="muted">Select a reply to see how it was produced: the route, the tools called with their arguments and results, the policy retrieved, and any escalation.</p>}
          {meta && (
            <div>
              <div className="kv"><span>Route</span><b>{meta.route}</b></div>
              {meta.route_reason && <div className="muted small">{meta.route_reason}</div>}
              <div className="kv"><span>Policies retrieved</span><b>{meta.policies_retrieved.join(', ') || 'none'}</b></div>
              <div className="kv"><span>Escalated to human</span><b>{meta.escalated ? 'yes' : 'no'}</b></div>
              {meta.pending_preference_consent && <div className="note">Waiting for the customer's consent before saving preferences.</div>}
              <h3>Tool calls ({meta.tools.length})</h3>
              {meta.tools.length === 0 && <p className="muted small">No tools were called for this reply.</p>}
              {meta.tools.map((t, i) => (
                <details key={i} className={t.ok ? 'tool' : 'tool bad'}>
                  <summary>{t.tool} {t.ok ? '' : '· error'}</summary>
                  <div className="lbl">Arguments</div><pre>{JSON.stringify(t.args, null, 2)}</pre>
                  <div className="lbl">Result</div><pre>{JSON.stringify(t.result, null, 2)}</pre>
                </details>
              ))}
            </div>
          )}
          <h2 className="mt">Saved preferences</h2>
          {prefs?.saved ? (
            <div>
              <pre>{JSON.stringify(prefs.preferences, null, 2)}</pre>
              <button className="ghost" onClick={deletePrefs}>Delete saved preferences</button>
            </div>
          ) : <p className="muted small">Nothing saved for this customer. Preferences are only saved with consent.</p>}
        </aside>}
      </div>
      <div className="footer">
        Independent prototype by Shalaka Bapat. This is a demo and is not affiliated with Armani Beauty, L'Oréal or Sierra. Customers are fictional; orders, returns and cases are simulated. Product and policy facts come from public pages captured 2026-11-02 and may have changed.
      </div>
    </div>
  )
}

// Small safe renderer for the advisor's replies: bullet lists, **bold**, *italic*, [label](url) and bare URLs.
// Builds React elements only (no innerHTML) and links only http(s).
function Rich({ text }) {
  const blocks = []
  let list = null
  for (const line of text.split('\n')) {
    const m = line.match(/^\s*(?:[-*\u2022]|\d+\.)\s+(.*)$/)
    if (m) { if (!list) { list = []; blocks.push({ list }) } list.push(m[1]) }
    else { list = null; if (line.trim()) blocks.push({ p: line }) }
  }
  return blocks.map((b, i) => b.list
    ? <ul key={i}>{b.list.map((li, k) => <li key={k}>{inline(li)}</li>)}</ul>
    : <p key={i}>{inline(b.p)}</p>)
}

function inline(s) {
  const re = /(\*\*[^*]+\*\*|\*[^*\n]+\*|\[[^\]]+\]\([^)\s]+\)|https?:\/\/[^\s)]*[^\s).,;:!?])/g
  const out = []
  let last = 0, m, n = 0
  while ((m = re.exec(s)) !== null) {
    if (m.index > last) out.push(s.slice(last, m.index))
    const t = m[0]
    if (t.startsWith('**')) out.push(<strong key={n++}>{inline(t.slice(2, -2))}</strong>)
    else if (t.startsWith('*')) out.push(<em key={n++}>{t.slice(1, -1)}</em>)
    else if (t.startsWith('[')) {
      const mm = t.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/)
      const href = /^https?:\/\//.test(mm[2]) ? mm[2] : /^[\w.-]+\.[a-z]{2,}(\/|$)/i.test(mm[2]) ? `https://${mm[2]}` : null
      out.push(href ? <a key={n++} href={href} target="_blank" rel="noreferrer">{mm[1]}</a> : mm[1])
    } else out.push(<a key={n++} href={t} target="_blank" rel="noreferrer">{t.replace(/^https?:\/\/(www\.)?/, '').slice(0, 48)}…</a>)
    last = m.index + t.length
  }
  if (last < s.length) out.push(s.slice(last))
  return out
}
