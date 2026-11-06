import { CalendarDays, ChevronDown, Clock3, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../../auth/useAuth";
import api, { errorMessage } from "../../api/client";
import MasteryBar from "../../components/MasteryBar";
import StageBadge from "../../components/StageBadge";

export default function ParentDashboard() {
  const { user } = useAuth();
  const [selectedChild, setSelectedChild] = useState(user?.linked_students?.[0] || "");
  const [children, setChildren] = useState([]);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const childIds = user?.linked_students || [];
    if (childIds.length < 2) return undefined;
    let active = true;
    Promise.all(childIds.map(async (id) => {
      const { data: childData } = await api.get(`/parent/child/${id}`);
      return { id, name: childData.child.name };
    }))
      .then((items) => active && setChildren(items))
      .catch((requestError) => active && setError(errorMessage(requestError)));
    return () => { active = false; };
  }, [user?.linked_students]);

  useEffect(() => {
    if (!selectedChild) return undefined;
    let active = true;
    api.get(`/parent/child/${selectedChild}`)
      .then(({ data: result }) => active && setData(result))
      .catch((requestError) => active && setError(errorMessage(requestError)));
    return () => { active = false; };
  }, [selectedChild]);

  const attendancePercent = data?.attendance?.length
    ? Math.round(data.attendance.filter((item) => item.present).length / data.attendance.length * 100)
    : 0;

  return (
    <div className="dashboard-page parent-page">
      <section className="welcome-band parent-welcome">
        <div><div className="eyebrow"><span /> FAMILY VIEW</div><h1>A clear view of their progress.</h1><p>Learning updates without answer-by-answer detail.</p></div>
        {user?.linked_students?.length > 1 && <label className="child-select"><span>CHILD</span><select value={selectedChild} onChange={(event) => setSelectedChild(event.target.value)}>{(children.length ? children : user.linked_students.map((id) => ({ id, name: id }))).map((child) => <option value={child.id} key={child.id}>{child.name}</option>)}</select><ChevronDown size={16} /></label>}
      </section>
      {error && <div className="notice error-notice" role="alert">{error}</div>}
      {user?.linked_students?.length === 0 ? <div className="empty-state">No linked child is available for this account.</div> : !data && !error ? <div className="loading-state">Loading progress...</div> : data && (
        <>
          <section className="parent-child-band"><div className="child-avatar">{data.child.name.slice(0, 1)}</div><div><div className="eyebrow">GRADE {data.child.grade || "—"}</div><h2>{data.child.name}</h2></div><span className="privacy-tag"><ShieldCheck size={15} /> Progress view</span></section>
          <div className="parent-summary-grid">
            <section className="data-section attendance-panel"><div className="section-heading"><div><div className="eyebrow">SCHOOL ROUTINE</div><h2>Attendance</h2></div><CalendarDays size={20} /></div><div className="attendance-figure"><strong>{attendancePercent}%</strong><span>present across recent records</span></div><div className="attendance-calendar">{data.attendance.slice(0, 14).reverse().map((entry) => <div key={entry.date} className={entry.present ? "day present" : "day absent"} title={`${entry.date}: ${entry.present ? "Present" : "Absent"}`}><span>{new Date(`${entry.date}T00:00:00`).getDate()}</span></div>)}</div><p className="small-note">Showing up can be affected by connectivity, shared devices and time.</p></section>
            <section className="data-section activity-panel"><div className="section-heading"><div><div className="eyebrow">RECENT ACTIVITY</div><h2>Last seen</h2></div><Clock3 size={20} /></div><div className="activity-time"><span className="activity-pulse" /><div><small>LAST LOGIN</small><strong>{data.recent_activity.last_login ? new Date(data.recent_activity.last_login).toLocaleString() : "No recent login"}</strong></div></div><div className="activity-time"><span className="activity-pulse coral-pulse" /><div><small>LAST LESSON</small><strong>{data.recent_activity.last_lesson ? new Date(data.recent_activity.last_lesson).toLocaleString() : "No lesson yet"}</strong></div></div><div className="privacy-rule"><ShieldCheck size={16} /> Answers and quiz details are private to the learner and teacher.</div></section>
          </div>
          <section className="data-section parent-progress"><div className="section-heading"><div><div className="eyebrow">CONCEPT JOURNEY</div><h2>Understanding & English support</h2></div></div><p className="stage-note-line">{data.stage_note}</p>
            {!data.progress.length ? <div className="empty-state">Progress will appear after the first lesson.</div> : <div className="parent-concept-list">{data.progress.map((item) => <div className="parent-concept" key={item.concept_id}><div><strong>{item.title || item.concept_id.replaceAll("_", " ")}</strong><StageBadge stage={item.stage} /></div><MasteryBar value={item.M} label="Understanding" /></div>)}</div>}
          </section>
        </>
      )}
    </div>
  );
}