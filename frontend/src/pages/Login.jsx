import { ArrowRight, BookOpenCheck, Languages, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { errorMessage } from "../api/client";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await login(email, password);
      navigate(`/${user.role}`, { replace: true });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-copy">
        <a className="brand-lockup login-brand" href="/login">
          <span className="brand-mark"><BookOpenCheck size={23} /></span>
          <span><strong>EduBridge</strong><small>LEARNING, IN CONTEXT</small></span>
        </a>
        <div className="login-message">
          <div className="eyebrow"><span /> A BRIDGE, ONE CONCEPT AT A TIME</div>
          <h1>Learn in the language that gets you there.</h1>
          <p>Build understanding first. Let English support grow with each concept.</p>
          <div className="language-ribbon"><Languages size={17} /><span>தமிழ்</span><i /> <span>മലയാളം</span><i /> <span>ಕನ್ನಡ</span><i /> <span>తెలుగు</span><i /> <span>English</span></div>
        </div>
        <div className="login-note"><ShieldCheck size={16} /> Private learning space for students, teachers and families</div>
      </section>
      <section className="login-panel">
        <div className="login-form-wrap">
          <div className="eyebrow">WELCOME BACK</div>
          <h2>Sign in to continue</h2>
          <p className="form-intro">Use the account provided by your school.</p>
          <form onSubmit={submit}>
            <label className="field-label" htmlFor="email">Email address</label>
            <input id="email" type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@school.edu" required />
            <label className="field-label" htmlFor="password">Password</label>
            <input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" required />
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="primary-button login-submit" type="submit" disabled={busy}>
              <span>{busy ? "Signing in..." : "Sign in"}</span><ArrowRight size={18} />
            </button>
          </form>
          <p className="login-footnote">The stage shows how much English support is provided, not English proficiency.</p>
        </div>
      </section>
    </main>
  );
}