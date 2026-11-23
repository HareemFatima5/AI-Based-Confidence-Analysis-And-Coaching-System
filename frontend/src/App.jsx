import { useEffect, useState } from 'react'
import { api } from './api'
import './styles.css'

const GOALS = [['interview', 'Job interviews'], ['viva', 'Viva and oral exams'], ['presentation', 'Class presentations'], ['public', 'Public speaking']]
const I = (d, s = 20) => <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">{d}</svg>
const Back = I(<path d="M15 5l-7 7 7 7" />)
const Mail = I(<><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3 8l9 6 9-6" /></>)
const User = I(<><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></>)
const Lock = I(<><rect x="5" y="11" width="14" height="10" rx="3" /><path d="M8 11V8a4 4 0 018 0v3" /></>)
const Eye = (off) => I(off ? <><path d="M3 3l18 18" /><path d="M10.6 6.2A9.7 9.7 0 0112 6c5 0 9 6 9 6a15 15 0 01-3 3.4M6.5 7.6C4 9.4 3 12 3 12s4 6 9 6c1.3 0 2.5-.3 3.6-.8" /></> : <><path d="M3 12s4-6 9-6 9 6 9 6-4 6-9 6-9-6-9-6z" /><circle cx="12" cy="12" r="3" /></>)

function CoachSvg() {
  return (
    <svg className="coach" viewBox="0 0 300 340" aria-hidden="true">
      <defs>
        <linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fcdcc3" /><stop offset="1" stopColor="#f0b693" /></linearGradient>
        <linearGradient id="bz" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8fd3ff" /><stop offset="1" stopColor="#4aa6ec" /></linearGradient>
        <linearGradient id="hr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#9a5236" /><stop offset="1" stopColor="#5a2a1b" /></linearGradient>
      </defs>
      <g className="spark" fill="#fff">
        <path d="M44 96l4 10 10 4-10 4-4 10-4-10-10-4 10-4z" /><path d="M262 70l3 8 8 3-8 3-3 8-3-8-8-3 8-3z" /><path d="M36 200l3 7 7 3-7 3-3 7-3-7-7-3 7-3z" />
      </g>
      <g className="hairback">
        <circle cx="150" cy="46" r="28" fill="url(#hr)" />
        <path d="M76 150C68 82 104 52 150 52s82 30 74 98c-3 34 8 60 0 96H76c-8-36 3-62 0-96z" fill="url(#hr)" />
      </g>
      <rect x="132" y="190" width="36" height="56" rx="14" fill="#f2bb98" />
      <path d="M34 340c2-66 44-96 116-100s114 34 116 100z" fill="url(#bz)" />
      <path d="M118 238l32 72 32-72z" fill="#fff" />
      <path d="M126 240l24 40 24-40z" fill="url(#sk)" />
      <path d="M118 238L98 270l34 44 18-4zM182 238l20 32-34 44-18-4z" fill="#3f98e0" />
      <circle cx="150" cy="326" r="4" fill="#fff" /><rect x="84" y="282" width="34" height="14" rx="7" fill="#fff" /><path d="M92 289h6l3-4 3 8 3-4h6" stroke="#4aa6ec" strokeWidth="2" fill="none" strokeLinecap="round" />
      <g className="head">
        <ellipse cx="99" cy="152" rx="9" ry="13" fill="#f4c3a0" /><ellipse cx="201" cy="152" rx="9" ry="13" fill="#f4c3a0" />
        <circle cx="99" cy="168" r="4" fill="#ffd36b" /><circle cx="201" cy="168" r="4" fill="#ffd36b" />
        <path d="M98 140c0-40 24-56 52-56s52 16 52 56c0 42-22 70-52 70s-52-28-52-70z" fill="url(#sk)" />
        <ellipse cx="112" cy="174" rx="11" ry="7" fill="#f59a9a" opacity=".45" /><ellipse cx="188" cy="174" rx="11" ry="7" fill="#f59a9a" opacity=".45" />
        <ellipse cx="126" cy="150" rx="9" ry="10" fill="#fff" /><ellipse cx="174" cy="150" rx="9" ry="10" fill="#fff" />
        <circle cx="127" cy="151" r="6.5" fill="#3a2216" /><circle cx="175" cy="151" r="6.5" fill="#3a2216" />
        <circle cx="129" cy="148" r="2" fill="#fff" /><circle cx="177" cy="148" r="2" fill="#fff" />
        <ellipse className="lid" cx="126" cy="150" rx="11" ry="12" fill="#f7cdaa" /><ellipse className="lid" cx="174" cy="150" rx="11" ry="12" fill="#f7cdaa" />
        <path d="M116 146q10-9 20 0M164 146q10-9 20 0" stroke="#3a2216" strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d="M112 128q14-9 28-2M160 126q14-7 28 2" stroke="#5a2a1b" strokeWidth="4" fill="none" strokeLinecap="round" />
        <g fill="#fff" fillOpacity=".16" stroke="#e23b4e" strokeWidth="4"><circle cx="126" cy="150" r="20" /><circle cx="174" cy="150" r="20" /></g>
        <path d="M146 148q4-4 8 0M106 148l-8-2M194 148l8-2" stroke="#e23b4e" strokeWidth="4" fill="none" strokeLinecap="round" />
        <path d="M150 162q-5 12 3 15" stroke="#e0a583" strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d="M132 186q18 22 36 0q-18 6-36 0z" fill="#fff" stroke="#c8465c" strokeWidth="3" strokeLinejoin="round" />
        <path d="M96 146C90 96 118 66 156 70c32 4 52 28 48 76-6-30-24-46-54-48-28 2-46 18-54 48z" fill="url(#hr)" />
        <path d="M122 82q22-14 50-4" stroke="#c07a55" strokeWidth="4" opacity=".5" fill="none" strokeLinecap="round" />
      </g>
      <g className="arm">
        <path d="M230 276C256 272 270 248 272 212" fill="none" stroke="#62b8f5" strokeWidth="32" strokeLinecap="round" />
        <path d="M272 212V178" stroke="#f6c8a5" strokeWidth="18" strokeLinecap="round" />
        <path d="M272 214v-8" stroke="#fff" strokeWidth="22" />
        <ellipse cx="272" cy="162" rx="15" ry="17" fill="#f6c8a5" />
        <g fill="#f6c8a5"><rect x="257" y="134" width="7" height="22" rx="3.5" /><rect x="265" y="130" width="7" height="26" rx="3.5" /><rect x="273" y="131" width="7" height="25" rx="3.5" /><rect x="281" y="137" width="7" height="20" rx="3.5" /><ellipse cx="256" cy="168" rx="5" ry="10" transform="rotate(-35 256 168)" /></g>
      </g>
    </svg>
  )
}

function Brand() {
  return (
    <div className="brand" aria-label="ConfiCoach">
      <span className="mark" aria-hidden="true"><i /><i /><i /><i /><i /></span>
      <span className="word">Confi<b>Coach</b></span>
    </div>
  )
}

function Coach() {
  const [ok, setOk] = useState(true)
  return ok
    ? <img className="coach photo" src="/coach.png" alt="" draggable="false" onError={() => setOk(false)} />
    : <CoachSvg />
}

// Sky-blue panel with the coach. Always shown on the login screen;
// on the other screens it only appears on desktop (desk = true).
function Hero({ desk }) {
  return (
    <div className={'hero' + (desk ? ' deskonly' : '')} aria-hidden={desk ? 'true' : undefined}>
      <i className="blob" style={{ width: 120, height: 120, left: -40, top: 60 }} /><i className="blob" style={{ width: 90, height: 90, right: -20, top: 30 }} />
      <Brand /><Coach />
    </div>
  )
}

function Field({ icon, type = 'text', value, onChange, placeholder, auto, pw }) {
  const [show, setShow] = useState(false)
  // Password fields must default to type="password"; only switch to text while "show" is on.
  const inputType = pw ? (show ? 'text' : 'password') : type
  return (
    <label className="in">
      <span style={{ color: '#9aa7ba', display: 'grid' }}>{icon}</span>
      <input type={inputType} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} autoComplete={auto} />
      {pw && <button type="button" className="ico" aria-label={show ? 'Hide password' : 'Show password'} aria-pressed={show} onClick={() => setShow(!show)}>{Eye(!show)}</button>}
    </label>
  )
}

const strong = p => p.length >= 10 && /[A-Za-z]/.test(p) && /\d/.test(p)
const okMail = e => /^\S+@\S+\.\S+$/.test(e)

function Login({ onAuth, flash, goSignup, goForgot }) {
  const [f, setF] = useState({ email: '', pw: '' })
  const [msg, setMsg] = useState(flash), [busy, setBusy] = useState(false)
  const submit = async e => {
    e.preventDefault()
    if (!okMail(f.email)) return setMsg({ t: 'err', m: 'Enter a valid email address.' })
    if (!f.pw) return setMsg({ t: 'err', m: 'Enter your password.' })
    setBusy(true); setMsg(null)
    try { onAuth(await api('login', { email: f.email.trim(), password: f.pw })) }
    catch (x) { setMsg({ t: 'err', m: x.message }) }
    setBusy(false)
  }
  return (
    <div className="phone">
      <Hero />
      <form className="sheet" onSubmit={submit} noValidate>
        <div className="cloud" />
        <h1>Log In</h1><p className="lead">Enter your account details to log in</p>
        {msg && <div className={'note ' + msg.t} role="alert">{msg.m}</div>}
        <Field icon={Mail} type="email" auto="email" placeholder="Email address" value={f.email} onChange={v => setF({ ...f, email: v })} />
        <Field icon={Lock} pw auto="current-password" placeholder="Password" value={f.pw} onChange={v => setF({ ...f, pw: v })} />
        <button type="button" className="link" style={{ margin: '4px auto 10px' }} onClick={goForgot}>Forgot Password?</button>
        <button className="btn" disabled={busy}>{busy ? 'Logging in...' : 'Log In'}</button>
        <button type="button" className="link" onClick={goSignup}>New here? <span>Create an account</span></button>
      </form>
    </div>
  )
}

function Signup({ goLogin }) {
  const [step, setStep] = useState(1)
  const [f, setF] = useState({ name: '', email: '', pw: '', goal: 'interview' })
  const [msg, setMsg] = useState(null), [busy, setBusy] = useState(false), [sent, setSent] = useState(false)
  const next = e => {
    e.preventDefault()
    if (f.name.trim().length < 2) return setMsg('Enter your full name.')
    if (!okMail(f.email)) return setMsg('Enter a valid email address.')
    if (!strong(f.pw)) return setMsg('Password needs 10+ characters with letters and numbers.')
    setMsg(null); setStep(2)
  }
  const create = async () => {
    setBusy(true); setMsg(null)
    try { await api('signup', { full_name: f.name.trim(), email: f.email.trim(), password: f.pw, practice_goal: f.goal }); setSent(true) }
    catch (x) { setMsg(x.message); setStep(1) }
    setBusy(false)
  }
  if (sent) return (
    <div className="phone"><Hero desk /><div className="main"><div className="page done" style={{ paddingTop: 110 }}>
      <div className="tick">{I(<path d="M5 12l5 5 9-10" />, 40)}</div>
      <h1>Check your email</h1>
      <p className="lead" style={{ margin: '10px 10px 28px' }}>We sent a verification link to <b>{f.email}</b>. Open it, then log in.</p>
      <button className="btn" onClick={goLogin}>Go to Log In</button>
    </div></div></div>
  )
  return (
    <div className="phone">
      <Hero desk />
      <div className="main">
        <div className="bar">
          <button className="round" aria-label="Back" onClick={() => (step === 1 ? goLogin() : setStep(1))}>{Back}</button>
          <div className="prog"><i style={{ width: step === 1 ? '45%' : '90%' }} /></div>
        </div>
        {step === 1 ? (
          <form className="page" onSubmit={next} noValidate>
            <div className="big">Create your<b>ConfiCoach account</b></div>
            {msg && <div className="note err" role="alert">{msg}</div>}
            <Field icon={User} auto="name" placeholder="Full name" value={f.name} onChange={v => setF({ ...f, name: v })} />
            <Field icon={Mail} type="email" auto="email" placeholder="Email address" value={f.email} onChange={v => setF({ ...f, email: v })} />
            <Field icon={Lock} pw auto="new-password" placeholder="Password (10+ characters)" value={f.pw} onChange={v => setF({ ...f, pw: v })} />
            <button className="btn">Continue</button>
          </form>
        ) : (
          <div className="page">
            <div className="big">What do you want<b>to practice for?</b></div>
            {msg && <div className="note err" role="alert">{msg}</div>}
            {GOALS.map(([k, label]) => (
              <button key={k} className={'opt' + (f.goal === k ? ' on' : '')} onClick={() => setF({ ...f, goal: k })}>{label}<i /></button>
            ))}
            <button className="btn" disabled={busy} onClick={create}>{busy ? 'Creating...' : 'Create account'}</button>
          </div>
        )}
      </div>
    </div>
  )
}

function Forgot({ goLogin }) {
  const [email, setEmail] = useState(''), [msg, setMsg] = useState(null), [busy, setBusy] = useState(false), [sent, setSent] = useState(false)
  const submit = async e => {
    e.preventDefault()
    if (!okMail(email)) return setMsg('Enter a valid email address.')
    setBusy(true); setMsg(null)
    try { await api('forgot', { email: email.trim() }); setSent(true) } catch (x) { setMsg(x.message) }
    setBusy(false)
  }
  if (sent) return (
    <div className="phone"><Hero desk /><div className="main"><div className="page done" style={{ paddingTop: 110 }}>
      <div className="tick">{I(<path d="M5 12l5 5 9-10" />, 40)}</div>
      <h1>Check your email</h1>
      <p className="lead" style={{ margin: '10px 10px 28px' }}>If an account exists for <b>{email}</b>, a reset link is on its way. It expires in 1 hour.</p>
      <button className="btn" onClick={goLogin}>Back to Log In</button>
    </div></div></div>
  )
  return (
    <div className="phone">
      <Hero desk />
      <div className="main">
        <div className="bar"><button className="round" aria-label="Back" onClick={goLogin}>{Back}</button><div className="prog"><i style={{ width: '50%' }} /></div></div>
        <form className="page" onSubmit={submit} noValidate>
          <div className="big">Forgot your<b>password?</b></div>
          <p className="lead" style={{ textAlign: 'left', margin: '-8px 0 18px' }}>Enter your email and we will send you a link to set a new one.</p>
          {msg && <div className="note err" role="alert">{msg}</div>}
          <Field icon={Mail} type="email" auto="email" placeholder="Email address" value={email} onChange={setEmail} />
          <button className="btn" disabled={busy}>{busy ? 'Sending...' : 'Send reset link'}</button>
        </form>
      </div>
    </div>
  )
}

function Reset({ token, done, goLogin }) {
  const [pw, setPw] = useState(''), [pw2, setPw2] = useState(''), [msg, setMsg] = useState(null), [busy, setBusy] = useState(false)
  const submit = async e => {
    e.preventDefault()
    if (!strong(pw)) return setMsg('Password needs 10+ characters with letters and numbers.')
    if (pw !== pw2) return setMsg('The two passwords do not match.')
    setBusy(true); setMsg(null)
    try { await api('reset', { token, password: pw }); done() } catch (x) { setMsg(x.message) }
    setBusy(false)
  }
  return (
    <div className="phone">
      <Hero desk />
      <div className="main">
        <div className="bar"><button className="round" aria-label="Back" onClick={goLogin}>{Back}</button><div className="prog"><i style={{ width: '85%' }} /></div></div>
        <form className="page" onSubmit={submit} noValidate>
          <div className="big">Set a new<b>password</b></div>
          {msg && <div className="note err" role="alert">{msg}</div>}
          <Field icon={Lock} pw auto="new-password" placeholder="New password (10+ characters)" value={pw} onChange={setPw} />
          <Field icon={Lock} pw auto="new-password" placeholder="Confirm new password" value={pw2} onChange={setPw2} />
          <button className="btn" disabled={busy}>{busy ? 'Saving...' : 'Update password'}</button>
        </form>
      </div>
    </div>
  )
}

function Dashboard({ user, onOut }) {
  const goal = (GOALS.find(g => g[0] === user.practice_goal) || GOALS[0])[1]
  return (
    <div className="phone">
      <div className="main">
        <div className="top">
          <div className="av">{user.full_name[0].toUpperCase()}</div>
          <button className="chip" onClick={onOut}>Log out</button>
        </div>
        <div className="page wide">
          <div className="big" style={{ marginBottom: 4 }}>Your confidence<b>journey starts here</b></div>
          <div className="chips">{['Overall', 'Speech', 'Voice', 'Face', 'Posture'].map((c, i) => <span key={c} className={'chip' + (i ? '' : ' on')}>{c}</span>)}</div>
          <div className="feat"><small>Step 1 of your plan</small><h3>Record a relaxed baseline video</h3><button>Start recording</button></div>
          <div className="grid2">
            <div className="mini">Practicing for<b style={{ fontSize: 16 }}>{goal}</b></div>
            <div className="mini">Sessions<b>0</b></div>
          </div>
        </div>
      </div>
      <div className="nav"><button aria-label="Sessions">{I(<path d="M4 6h16M4 12h16M4 18h10" />)}</button><button className="home" aria-label="Home">{I(<path d="M4 11l8-7 8 7v9H4z" />, 24)}</button><button aria-label="Profile">{I(<><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></>)}</button></div>
    </div>
  )
}

export default function App() {
  const [view, setView] = useState('boot'), [user, setUser] = useState(null), [flash, setFlash] = useState(null), [tok, setTok] = useState('')
  useEffect(() => {
    const q = new URLSearchParams(location.search), v = q.get('verified'), r = q.get('reset')
    if (v || r) history.replaceState(null, '', '/')
    if (r) { setTok(r); setView('reset'); return }
    if (v) setFlash(v === '1' ? { t: 'ok', m: 'Email verified. You can log in now.' } : { t: 'err', m: 'That link is invalid or expired. Please sign up again.' })
    api('me').then(u => { setUser(u); setView('app') }).catch(() => setView('login'))
  }, [])
  const toLogin = () => setView('login')
  if (view === 'boot') return null
  if (view === 'signup') return <Signup goLogin={toLogin} />
  if (view === 'forgot') return <Forgot goLogin={toLogin} />
  if (view === 'reset') return <Reset token={tok} goLogin={toLogin} done={() => { setFlash({ t: 'ok', m: 'Password updated. Log in with your new password.' }); setView('login') }} />
  if (view === 'app' && user) return <Dashboard user={user} onOut={async () => { await api('logout', {}); setUser(null); setView('login') }} />
  return <Login flash={flash} goSignup={() => setView('signup')} goForgot={() => setView('forgot')} onAuth={async () => { setUser(await api('me')); setView('app') }} />
}
