import { ArrowRight, BookOpenCheck, Languages, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { errorMessage } from "../api/client";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [language, setLanguage] = useState("ta");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const registering = mode === "register";

  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = registering
        ? await register(name, email, password, language)
        : await login(email, password);
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
          <div className="eyebrow">{registering ? "CREATE A STUDENT ACCOUNT" : "WELCOME BACK"}</div>
          <h2>{registering ? "Start learning with EduBridge" : "Sign in to continue"}</h2>
          <p className="form-intro">{registering ? "Create an account for CBSE Class 10." : "Use your school account or create a student account."}</p>
          <form onSubmit={submit}>
            {registering && (
              <>
                <label className="field-label" htmlFor="name">Full name</label>
                <input id="name" type="text" autoComplete="name" maxLength={120} value={name} onChange={(event) => setName(event.target.value)} placeholder="Your name" required />
              </>
            )}
            <label className="field-label" htmlFor="email">Email address</label>
            <input id="email" type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@school.edu" required />
            {registering && (
              <>
                <label className="field-label" htmlFor="language">Learning language</label>
                <select id="language" value={language} onChange={(event) => setLanguage(event.target.value)}>
                  <option value="ta">Tamil</option>
                  <option value="ml">Malayalam</option>
                  <option value="kn">Kannada</option>
                  <option value="te">Telugu</option>
                  <option value="en">English</option>
                </select>
              </>
            )}
            <label className="field-label" htmlFor="password">Password</label>
            <input id="password" type="password" autoComplete={registering ? "new-password" : "current-password"} minLength={registering ? 10 : 8} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={registering ? "At least 10 characters" : "Enter your password"} required />
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="primary-button login-submit" type="submit" disabled={busy}>
              <span>{busy ? (registering ? "Creating account..." : "Signing in...") : (registering ? "Create account" : "Sign in")}</span><ArrowRight size={18} />
            </button>
          </form>
          <p className="auth-mode-switch">
            {registering ? "Already have an account?" : "New student?"}{" "}
            <button type="button" onClick={() => { setMode(registering ? "login" : "register"); setError(""); }}>
              {registering ? "Sign in" : "Create a student account"}
            </button>
          </p>
          {registering && <p className="registration-note">Public sign-up is for students only. For real student data, obtain school approval and parental consent first.</p>}
          <p className="login-footnote">The stage shows how much English support is provided, not English proficiency.</p>
        </div>
      </section>
    </main>
  );
}