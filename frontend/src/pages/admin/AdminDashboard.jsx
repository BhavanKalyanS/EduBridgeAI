import { Activity, BookOpenText, Database, KeyRound, Pencil, Plus, ShieldCheck, Trash2, Users } from "lucide-react";
import { useEffect, useState } from "react";
import api, { errorMessage } from "../../api/client";

const tabs = ["Users", "Classes", "Curriculum", "Settings", "Events & audit"];

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [classes, setClasses] = useState([]);
  const [concepts, setConcepts] = useState([]);
  const [events, setEvents] = useState([]);
  const [audit, setAudit] = useState([]);
  const [privacyRequests, setPrivacyRequests] = useState([]);
  const [settings, setSettings] = useState(null);
  const [tab, setTab] = useState("Users");
  const [showUserForm, setShowUserForm] = useState(false);
  const [passwordTarget, setPasswordTarget] = useState("");
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [classForm, setClassForm] = useState({ class_id: "", name: "", teacher_id: "", student_ids: [] });
  const [editingClass, setEditingClass] = useState("");
  const [selectedConcept, setSelectedConcept] = useState("");
  const [newUser, setNewUser] = useState({ name: "", email: "", password: "", role: "student", language: "ta", grade: "10", linked_students: [] });
  const [conceptJson, setConceptJson] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [overviewResponse, usersResponse, classesResponse, conceptsResponse, settingsResponse, eventsResponse, auditResponse, privacyResponse] = await Promise.all([
        api.get("/admin/overview"), api.get("/admin/users"), api.get("/admin/classes"), api.get("/admin/curriculum"), api.get("/admin/settings"), api.get("/admin/events?limit=50"), api.get("/admin/audit"), api.get("/admin/privacy-requests"),
      ]);
      setOverview(overviewResponse.data);
      setUsers(usersResponse.data.users);
      setClasses(classesResponse.data.classes);
      setConcepts(conceptsResponse.data.concepts);
      setSettings(settingsResponse.data.settings);
      setEvents(eventsResponse.data.events);
      setAudit(auditResponse.data.entries);
      setPrivacyRequests(privacyResponse.data.requests);
      setConceptJson(JSON.stringify({
        concept_id: "cbse10_math_quadratic", subject: "Mathematics", grade: "10", board: "CBSE", chapter: "Algebra", lesson: "Quadratic equations",
        title: { en: "Quadratic equations", ta: "இருபடி சமன்பாடுகள்", ml: "", kn: "", te: "" },
        keywords: [{ en: "variable", ta: "மாறி", ml: "", kn: "", te: "" }],
        content: { ta: { s0: "", s1: "", s2: "", s3: "", s4: "" } },
        quiz: [{ q_id: "q1", kind: "concept", question: { ta: "" }, options: ["A", "B"], answer: "A" }],
        review_status: "draft",
      }, null, 2));
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  useEffect(() => { queueMicrotask(() => { void load(); }); }, []);

  async function createUser(event) {
    event.preventDefault();
    setError(""); setMessage("");
    try {
      await api.post("/admin/users", newUser);
      setMessage("Account created.");
      setShowUserForm(false);
      setNewUser({ name: "", email: "", password: "", role: "student", language: "ta", grade: "10", linked_students: [] });
      await load();
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  async function deactivateUser(user) {
    if (!window.confirm(`Deactivate ${user.name}?`)) return;
    try {
      await api.delete(`/admin/users/${user.id}`);
      setMessage(`${user.name} deactivated.`);
      await load();
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  async function saveConcept(event) {
    event.preventDefault(); setError(""); setMessage("");
    try {
      const data = JSON.parse(conceptJson);
      if (selectedConcept) await api.put(`/admin/curriculum/${selectedConcept}`, data);
      else await api.post("/admin/curriculum", data);
      setMessage(selectedConcept ? "Concept updated." : "Concept created.");
      setSelectedConcept("");
      await load();
    } catch (requestError) {
      setError(requestError instanceof SyntaxError ? "Curriculum must be valid JSON." : errorMessage(requestError));
    }
  }

  async function saveClass(event) {
    event.preventDefault(); setError(""); setMessage("");
    try {
      const endpoint = editingClass ? `/admin/classes/${editingClass}` : "/admin/classes";
      if (editingClass) await api.put(endpoint, classForm);
      else await api.post(endpoint, classForm);
      setMessage(editingClass ? "Class updated." : "Class created.");
      setEditingClass("");
      setClassForm({ class_id: "", name: "", teacher_id: "", student_ids: [] });
      await load();
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  async function deleteClass(schoolClass) {
    if (!window.confirm(`Delete ${schoolClass.name}?`)) return;
    try {
      await api.delete(`/admin/classes/${schoolClass.class_id}`);
      setMessage(`${schoolClass.name} deleted.`);
      await load();
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  async function toggleConsent(user) {
    try {
      await api.patch(`/admin/users/${user.id}`, { consent: !user.consent });
      setMessage(`Consent status updated for ${user.name}.`);
      await load();
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  async function resetPassword(user) {
    if (temporaryPassword.length < 10) {
      setError("Temporary passwords must contain at least 10 characters.");
      return;
    }
    try {
      await api.patch(`/admin/users/${user.id}`, { password: temporaryPassword });
      setMessage(`Temporary password updated for ${user.name}.`);
      setPasswordTarget("");
      setTemporaryPassword("");
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  function editConcept(concept) {
    const { id: _id, ...document } = concept;
    setSelectedConcept(concept.concept_id);
    setConceptJson(JSON.stringify(document, null, 2));
  }

  async function deleteConcept(concept) {
    if (!window.confirm(`Delete ${concept.title?.en || concept.concept_id}?`)) return;
    try {
      await api.delete(`/admin/curriculum/${concept.concept_id}`);
      setMessage("Concept deleted.");
      if (selectedConcept === concept.concept_id) setSelectedConcept("");
      await load();
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  async function saveSettings(event) {
    event.preventDefault(); setError(""); setMessage("");
    try {
      await api.put("/admin/settings", settings);
      setMessage("Learning settings saved. Parameters remain labelled untuned.");
      await load();
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  function setNumber(group, key, value) {
    setSettings((current) => ({ ...current, [group]: { ...current[group], [key]: Number(value) } }));
  }

  return (
    <div className="dashboard-page admin-page">
      <section className="welcome-band admin-welcome"><div><div className="eyebrow"><span /> SYSTEM CONTROL</div><h1>Keep the learning system in view.</h1><p>Accounts, curriculum review, learning rules and audit activity.</p></div><div className="welcome-number"><span>{overview?.concepts ?? "—"}</span><small>CURRICULUM<br />CONCEPTS</small></div></section>
      {error && <div className="notice error-notice" role="alert">{error}</div>}{message && <div className="notice success-notice" role="status">{message}</div>}
      <div className="metric-strip admin-metrics">
        <div className="metric-item"><span className="metric-mark mark-teal"><Users size={17} /></span><div><strong>{overview?.users ?? "—"}</strong><small>Active users</small></div></div>
        <div className="metric-item"><span className="metric-mark mark-coral"><Database size={17} /></span><div><strong>{overview?.classes ?? "—"}</strong><small>Classes</small></div></div>
        <div className="metric-item"><span className="metric-mark mark-lime"><BookOpenText size={17} /></span><div><strong>{overview?.concepts ?? "—"}</strong><small>Concepts</small></div></div>
        <div className="system-status"><span className="status-live" /> Database connected</div>
      </div>
      <div className="admin-tabs" role="tablist" aria-label="Administration sections">{tabs.map((item) => <button key={item} type="button" role="tab" aria-selected={tab === item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>{item}</button>)}</div>

      {tab === "Users" && <section className="data-section admin-table-section">
        <div className="section-heading"><div><div className="eyebrow">IDENTITY & ACCESS</div><h2>User accounts</h2></div><button className="primary-button compact-button" type="button" onClick={() => setShowUserForm((value) => !value)}><Plus size={16} /> Add user</button></div>
        {showUserForm && <form className="inline-form user-create-form" onSubmit={createUser}>
          <label>Name<input required value={newUser.name} onChange={(event) => setNewUser({ ...newUser, name: event.target.value })} /></label>
          <label>Email<input required type="email" value={newUser.email} onChange={(event) => setNewUser({ ...newUser, email: event.target.value })} /></label>
          <label>Temporary password<input required type="password" minLength="10" value={newUser.password} onChange={(event) => setNewUser({ ...newUser, password: event.target.value })} /></label>
          <label>Role<select value={newUser.role} onChange={(event) => setNewUser({ ...newUser, role: event.target.value })}>{["student", "teacher", "parent", "admin"].map((role) => <option key={role}>{role}</option>)}</select></label>
          <label>Language<select value={newUser.language} onChange={(event) => setNewUser({ ...newUser, language: event.target.value })}>{[["ta", "Tamil"], ["ml", "Malayalam"], ["kn", "Kannada"], ["te", "Telugu"], ["en", "English"]].map(([value, name]) => <option value={value} key={value}>{name}</option>)}</select></label>
          <label>Grade<input value={newUser.grade} onChange={(event) => setNewUser({ ...newUser, grade: event.target.value })} /></label>
          {newUser.role === "parent" && <label>Linked students<select multiple value={newUser.linked_students} onChange={(event) => setNewUser({ ...newUser, linked_students: Array.from(event.target.selectedOptions, (option) => option.value) })}>{users.filter((user) => user.role === "student" && user.active).map((student) => <option value={student.id} key={student.id}>{student.name}</option>)}</select></label>}
          <div className="form-actions"><button className="primary-button compact-button" type="submit">Create account</button></div>
        </form>}
        <div className="table-wrap"><table><thead><tr><th>NAME</th><th>EMAIL</th><th>ROLE</th><th>LANGUAGE</th><th>CONSENT</th><th>STATUS</th><th /></tr></thead><tbody>
          {users.map((user) => <tr key={user.id}><td><span className="admin-user-name"><span className="avatar small-avatar">{user.name.slice(0, 1)}</span>{user.name}</span></td><td>{user.email}</td><td><span className={`role-tag role-${user.role}`}>{user.role}</span></td><td>{user.language?.toUpperCase()}</td><td><button className={`consent-toggle ${user.consent ? "granted" : "not-granted"}`} type="button" onClick={() => toggleConsent(user)}>{user.consent ? "Granted" : "Not recorded"}</button></td><td><span className={user.active ? "active-status" : "inactive-status"}>{user.active ? "Active" : "Inactive"}</span></td><td>{user.active && <div className="account-actions">{passwordTarget === user.id ? <div className="password-reset"><input type="password" minLength="10" value={temporaryPassword} onChange={(event) => setTemporaryPassword(event.target.value)} aria-label={`Temporary password for ${user.name}`} placeholder="10+ characters" /><button className="text-button" type="button" onClick={() => resetPassword(user)}>Save</button><button className="text-button danger-text" type="button" onClick={() => { setPasswordTarget(""); setTemporaryPassword(""); }}>Cancel</button></div> : <button className="text-button" type="button" onClick={() => { setPasswordTarget(user.id); setTemporaryPassword(""); }}>Reset password</button>}<button className="text-button danger-text" type="button" onClick={() => deactivateUser(user)}>Deactivate</button></div>}</td></tr>)}
        </tbody></table></div>
      </section>}

      {tab === "Classes" && <section className="data-section class-admin-section">
        <div className="section-heading"><div><div className="eyebrow">CLASS ROSTERS</div><h2>Classes</h2></div></div>
        <form className="inline-form class-create-form" onSubmit={saveClass}>
          <label>Class ID<input required disabled={Boolean(editingClass)} value={classForm.class_id} onChange={(event) => setClassForm({ ...classForm, class_id: event.target.value })} /></label>
          <label>Class name<input required value={classForm.name} onChange={(event) => setClassForm({ ...classForm, name: event.target.value })} /></label>
          <label>Teacher<select required value={classForm.teacher_id} onChange={(event) => setClassForm({ ...classForm, teacher_id: event.target.value })}><option value="">Choose teacher</option>{users.filter((user) => user.role === "teacher" && user.active).map((teacher) => <option value={teacher.id} key={teacher.id}>{teacher.name}</option>)}</select></label>
          <label>Students<select multiple value={classForm.student_ids} onChange={(event) => setClassForm({ ...classForm, student_ids: Array.from(event.target.selectedOptions, (option) => option.value) })}>{users.filter((user) => user.role === "student" && user.active).map((student) => <option value={student.id} key={student.id}>{student.name}</option>)}</select></label>
          <div className="form-actions"><button className="primary-button compact-button" type="submit">{editingClass ? "Save class" : "Create class"}</button>{editingClass && <button className="text-button" type="button" onClick={() => { setEditingClass(""); setClassForm({ class_id: "", name: "", teacher_id: "", student_ids: [] }); }}>Cancel</button>}</div>
        </form>
        <div className="table-wrap"><table><thead><tr><th>CLASS</th><th>TEACHER</th><th>STUDENTS</th><th /></tr></thead><tbody>{classes.map((schoolClass) => <tr key={schoolClass.class_id}><td><strong>{schoolClass.name}</strong><small className="table-secondary">{schoolClass.class_id}</small></td><td>{users.find((user) => user.id === schoolClass.teacher_id)?.name || "Unassigned"}</td><td>{schoolClass.student_ids.length}</td><td className="row-actions"><button className="icon-button" type="button" onClick={() => { setEditingClass(schoolClass.class_id); setClassForm({ class_id: schoolClass.class_id, name: schoolClass.name, teacher_id: schoolClass.teacher_id, student_ids: schoolClass.student_ids }); }} aria-label={`Edit ${schoolClass.name}`} title="Edit class"><Pencil size={14} /></button><button className="icon-button" type="button" onClick={() => deleteClass(schoolClass)} aria-label={`Delete ${schoolClass.name}`} title="Delete class"><Trash2 size={14} /></button></td></tr>)}</tbody></table></div>
      </section>}

      {tab === "Curriculum" && <section className="curriculum-admin-grid"><div className="data-section">
        <div className="section-heading"><div><div className="eyebrow">CONTENT REVIEW</div><h2>Curriculum library</h2></div><span className="item-count">{concepts.length} CONCEPTS</span></div>
        <div className="table-wrap"><table><thead><tr><th>CONCEPT</th><th>SUBJECT</th><th>CHAPTER</th><th>REVIEW</th><th /></tr></thead><tbody>{concepts.map((concept) => <tr key={concept.concept_id}><td>{concept.title?.en || concept.concept_id}</td><td>{concept.subject}</td><td>{concept.chapter}</td><td><span className={`review-tag review-${concept.review_status}`}>{concept.review_status}</span></td><td className="row-actions"><button className="icon-button" type="button" onClick={() => editConcept(concept)} aria-label={`Edit ${concept.concept_id}`} title="Edit concept"><Pencil size={14} /></button><button className="icon-button" type="button" onClick={() => deleteConcept(concept)} aria-label={`Delete ${concept.concept_id}`} title="Delete concept"><Trash2 size={14} /></button></td></tr>)}</tbody></table></div>
      </div><form className="data-section curriculum-editor" onSubmit={saveConcept}><div className="eyebrow">CONTENT EDITOR</div><h2>{selectedConcept ? "Edit concept" : "Add a concept"}</h2><label className="field-label" htmlFor="curriculum-json">Curriculum document</label><textarea id="curriculum-json" spellCheck="false" value={conceptJson} onChange={(event) => setConceptJson(event.target.value)} rows="21" /><div className="curriculum-actions"><button className="primary-button compact-button" type="submit">{selectedConcept ? "Save changes" : "Save as draft"}</button>{selectedConcept && <button className="text-button" type="button" onClick={() => { setSelectedConcept(""); setConceptJson(""); }}>New concept</button>}</div></form></section>}

      {tab === "Settings" && settings && <section className="data-section settings-section"><div className="section-heading"><div><div className="eyebrow">RULES & PARAMETERS</div><h2>Learning settings</h2></div><span className="untuned-pill"><KeyRound size={14} /> UNTUNED DEFAULTS</span></div><p className="section-subtitle">These are configurable placeholders. They are not validated learning parameters.</p>
        <form onSubmit={saveSettings}><div className="settings-groups"><fieldset><legend>BKT parameters</legend>{[["P0", "Initial knowledge"], ["T", "Learning transition"], ["g", "Guess"], ["s", "Slip"]].map(([key, label]) => <label className="setting-control" key={key}><span>{label}<small>{key}</small></span><input type="number" min="0" max="1" step="0.01" value={settings.bkt[key]} onChange={(event) => setNumber("bkt", key, event.target.value)} /></label>)}</fieldset><fieldset><legend>Stage thresholds</legend>{[["promote_M", "Promote concept mastery"], ["promote_L", "Promote keyword mastery"], ["regress_M", "Regress concept mastery"], ["streak", "Answer streak"]].map(([key, label]) => <label className="setting-control" key={key}><span>{label}<small>{key}</small></span><input type="number" min="0" max={key === "streak" ? "5" : "1"} step={key === "streak" ? "1" : "0.01"} value={settings.thresholds[key]} onChange={(event) => setNumber("thresholds", key, event.target.value)} /></label>)}</fieldset></div><button className="primary-button compact-button" type="submit">Save settings</button></form>
      </section>}

      {tab === "Events & audit" && <div className="audit-grid">
        <section className="data-section"><div className="section-heading"><div><div className="eyebrow">APPEND-ONLY RECORD</div><h2>Answer events</h2></div><Activity size={18} /></div><div className="table-wrap"><table><thead><tr><th>EVENT</th><th>CONCEPT</th><th>RESULT</th><th>VALID</th></tr></thead><tbody>{events.map((event) => <tr key={event.id}><td className="mono-cell">{event.event_id?.slice(0, 12)}</td><td>{event.concept_id}</td><td>{event.correct == null ? event.reason : event.correct ? "Correct" : "Incorrect"}</td><td><span className={event.valid ? "active-status" : "inactive-status"}>{event.valid ? "Valid" : "Rejected"}</span></td></tr>)}</tbody></table></div></section>
        <section className="data-section"><div className="section-heading"><div><div className="eyebrow">CHANGE HISTORY</div><h2>Audit log</h2></div><ShieldCheck size={18} /></div><div className="audit-list">{audit.map((entry) => <div key={entry.id}><span className="audit-dot" /><div><strong>{entry.action}</strong><small>{entry.target}</small></div><time>{entry.ts ? new Date(entry.ts).toLocaleString() : ""}</time></div>)}</div></section>
        <section className="data-section privacy-requests"><div className="section-heading"><div><div className="eyebrow">DATA RIGHTS</div><h2>Privacy requests</h2></div></div>{privacyRequests.length ? privacyRequests.map((item) => <div className="privacy-request-row" key={item.id}><span>{item.user_id}</span><span className="review-tag">{item.status}</span></div>) : <p className="muted-copy">No pending requests.</p>}</section>
      </div>}
    </div>
  );
}