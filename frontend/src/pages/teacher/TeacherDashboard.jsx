import { Activity, CalendarCheck, Search, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api, { errorMessage } from "../../api/client";
import MasteryBar from "../../components/MasteryBar";
import StageBadge from "../../components/StageBadge";

export default function TeacherDashboard() {
  const [summary, setSummary] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [distributionConcept, setDistributionConcept] = useState("");
  const [query, setQuery] = useState("");
  const [detail, setDetail] = useState(null);
  const [attendance, setAttendance] = useState({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const { data: userData } = await api.get("/auth/me");
      const classId = userData.user.class_id;
      if (!classId) { setSummary({ students: [], student_count: 0, average_mastery: 0, weekly_activity: 0 }); return; }
      const attendanceDate = new Date().toISOString().slice(0, 10);
      const [summaryResponse, heatmapResponse, attendanceResponse] = await Promise.all([
        api.get(`/teacher/class/${classId}/summary`),
        api.get(`/teacher/class/${classId}/heatmap`),
        api.get(`/teacher/attendance?date=${attendanceDate}`),
      ]);
      setSummary(summaryResponse.data);
      setHeatmap(heatmapResponse.data);
      setAttendance(Object.fromEntries(summaryResponse.data.students.map((student) => [student.id, attendanceResponse.data.attendance[student.id] ?? false])));
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  useEffect(() => { queueMicrotask(() => { void load(); }); }, []);

  async function openStudent(studentId) {
    try {
      const { data } = await api.get(`/teacher/student/${studentId}`);
      setDetail(data);
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  async function saveAttendance() {
    if (!summary?.students?.length) return;
    try {
      const date = new Date().toISOString().slice(0, 10);
      const { data } = await api.post("/teacher/attendance", {
        date,
        entries: summary.students.map((student) => ({ user_id: student.id, present: Boolean(attendance[student.id]) })),
      });
      setMessage(`Attendance saved for ${data.saved} students.`);
    } catch (requestError) { setError(errorMessage(requestError)); }
  }

  const filteredStudents = (summary?.students || []).filter((student) => student.name.toLowerCase().includes(query.toLowerCase()));
  const selectedDistributionConcept = distributionConcept || heatmap?.concepts?.[0]?.concept_id;
  const stageCounts = [0, 1, 2, 3, 4].map((stage) => ({
    name: `S${stage}`,
    students: (heatmap?.students || []).filter((student) => student.stages?.[selectedDistributionConcept] === stage).length,
  }));
  const supportItems = (heatmap?.concepts || []).map((concept) => {
    const records = heatmap.students.map((student) => ({
      M: student.mastery[concept.concept_id],
      L: student.keyword_mastery?.[concept.concept_id],
    }));
    return {
      ...concept,
      needsSupport: records.filter((record) => record.M != null && record.M < 0.40).length,
      vocabularySupport: records.filter((record) => record.M != null && record.M >= 0.85 && record.L != null && record.L < 0.70).length,
    };
  });
  const needsSupport = supportItems.filter((item) => item.needsSupport > 0).sort((a, b) => b.needsSupport - a.needsSupport);
  const vocabularySupport = supportItems.filter((item) => item.vocabularySupport > 0).sort((a, b) => b.vocabularySupport - a.vocabularySupport);

  return (
    <div className="dashboard-page teacher-page">
      <section className="welcome-band teacher-welcome">
        <div><div className="eyebrow"><span /> TEACHER WORKSPACE</div><h1>See where learning is moving.</h1><p>Class progress by concept, with support needs kept visible and explainable.</p></div>
        <div className="welcome-number"><span>{summary?.student_count ?? "—"}</span><small>STUDENTS<br />IN CLASS</small></div>
      </section>
      {error && <div className="notice error-notice" role="alert">{error}</div>}
      {message && <div className="notice success-notice" role="status">{message}</div>}

      <div className="metric-strip teacher-metrics">
        <div className="metric-item"><span className="metric-mark mark-teal"><Users size={17} /></span><div><strong>{summary?.student_count ?? "—"}</strong><small>Students</small></div></div>
        <div className="metric-item"><span className="metric-mark mark-lime"><Activity size={17} /></span><div><strong>{summary ? `${Math.round(summary.average_mastery * 100)}%` : "—"}</strong><small>Average understanding</small></div></div>
        <div className="metric-item"><span className="metric-mark mark-coral"><CalendarCheck size={17} /></span><div><strong>{summary?.weekly_activity ?? "—"}</strong><small>Answers this week</small></div></div>
      </div>

      <div className="teacher-grid">
        <section className="data-section student-roster">
          <div className="section-heading"><div><div className="eyebrow">CLASS LIST</div><h2>Students</h2></div><label className="search-box"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find a student" aria-label="Find a student" /></label></div>
          {!filteredStudents.length ? <div className="empty-state">No students are assigned to your class yet.</div> : (
            <div className="table-wrap"><table><thead><tr><th>STUDENT</th><th>UNDERSTANDING</th><th>CONCEPTS</th><th>ATTENDANCE</th><th /></tr></thead><tbody>
              {filteredStudents.map((student) => (
                <tr key={student.id}>
                  <td><button className="student-name-button" type="button" onClick={() => openStudent(student.id)}><span className="avatar small-avatar">{student.name.slice(0, 1)}</span>{student.name}</button></td>
                  <td><span className="table-percent">{Math.round(student.average_mastery * 100)}%</span></td>
                  <td>{(heatmap?.students.find((entry) => entry.student_id === student.id)?.mastery && Object.keys(heatmap.students.find((entry) => entry.student_id === student.id).mastery).length) || 0}</td>
                  <td><label className="attendance-check"><input type="checkbox" checked={Boolean(attendance[student.id])} onChange={(event) => setAttendance((current) => ({ ...current, [student.id]: event.target.checked }))} /><span>Present</span></label></td>
                  <td><button className="icon-button" type="button" onClick={() => openStudent(student.id)} aria-label={`View ${student.name}`} title="View student"><span>→</span></button></td>
                </tr>
              ))}
            </tbody></table></div>
          )}
          <div className="roster-footer"><span>{filteredStudents.length} students shown</span><button className="text-button" type="button" onClick={saveAttendance}>Save today’s attendance <span>→</span></button></div>
        </section>
        <section className="data-section distribution-panel">
          <div className="section-heading"><div><div className="eyebrow">CLASS PICTURE</div><h2>Stage distribution</h2></div><label className="distribution-select"><span className="sr-only">Concept</span><select aria-label="Distribution concept" value={selectedDistributionConcept || ""} onChange={(event) => setDistributionConcept(event.target.value)} disabled={!heatmap?.concepts?.length}>{(heatmap?.concepts || []).map((concept) => <option value={concept.concept_id} key={concept.concept_id}>{concept.title || concept.concept_id}</option>)}</select></label></div>
          <p className="section-subtitle">Students grouped by current English-support stage.</p>
          <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><BarChart data={stageCounts} margin={{ top: 8, right: 4, bottom: 0, left: -20 }}>
            <CartesianGrid vertical={false} stroke="#e7ebe5" />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: "#718078", fontSize: 11 }} />
            <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: "#718078", fontSize: 11 }} />
            <Tooltip cursor={{ fill: "#f3f5ef" }} />
            <Bar dataKey="students" fill="#1f867a" radius={[4, 4, 0, 0]} maxBarSize={34} />
          </BarChart></ResponsiveContainer></div>
          <div className="stage-chart-legend"><span><i className="legend-dot teal-dot" /> English-support stage, not proficiency</span></div>
        </section>
      </div>

      <section className="data-section heatmap-section">
        <div className="section-heading"><div><div className="eyebrow">CONCEPT VIEW</div><h2>Understanding by concept</h2></div><span className="item-count">{heatmap?.concepts?.length || 0} CONCEPTS</span></div>
        {!heatmap?.concepts?.length ? <div className="empty-state">Approved curriculum will appear here.</div> : (
          <div className="heatmap-scroll"><table className="heatmap-table"><thead><tr><th>STUDENT</th>{heatmap.concepts.map((concept) => <th key={concept.concept_id} title={concept.title}>{concept.title || concept.concept_id}</th>)}</tr></thead><tbody>
            {heatmap.students.map((student) => <tr key={student.student_id}><th>{student.name}</th>{heatmap.concepts.map((concept) => { const value = student.mastery[concept.concept_id]; return <td key={concept.concept_id}><span title={value == null ? "Not started" : `${Math.round(value * 100)}%`} style={{ backgroundColor: value == null ? "#f1f3ef" : `rgba(31, 134, 122, ${0.08 + value * 0.72})` }}>{value == null ? "—" : Math.round(value * 100)}</span></td>; })}</tr>)}
          </tbody></table></div>
        )}
      </section>

      <div className="support-grid">
        <section className="data-section"><div className="section-heading"><div><div className="eyebrow">CONCEPT MASTERY</div><h2>Concepts needing support</h2></div></div>
          {needsSupport.length ? <div className="support-list">{needsSupport.map((item) => <div key={item.concept_id}><span className="support-symbol">!</span><strong>{item.title || item.concept_id}</strong><span>{item.needsSupport} students</span></div>)}</div> : <p className="muted-copy">No concepts are below the current support threshold.</p>}
        </section>
        <section className="data-section"><div className="section-heading"><div><div className="eyebrow">KEYWORD MASTERY</div><h2>Vocabulary support</h2></div></div>
          {vocabularySupport.length ? <div className="support-list">{vocabularySupport.map((item) => <div key={item.concept_id}><span className="support-symbol vocab-symbol">Aa</span><strong>{item.title || item.concept_id}</strong><span>{item.vocabularySupport} students</span></div>)}</div> : <p className="muted-copy">No vocabulary-support flags are active.</p>}
        </section>
      </div>

      {detail && <div className="modal-backdrop" role="presentation" onClick={() => setDetail(null)}><section className="student-detail-modal" role="dialog" aria-modal="true" aria-label="Student detail" onClick={(event) => event.stopPropagation()}>
        <div className="modal-heading"><div><div className="eyebrow">STUDENT DETAIL</div><h2>{detail.student.name}</h2></div><button className="icon-button" type="button" onClick={() => setDetail(null)} aria-label="Close detail">×</button></div>
        <div className="detail-progress-list">{detail.mastery.map((item) => <div className="detail-progress" key={item.concept_id}><div><strong>{item.concept_id}</strong><StageBadge stage={item.stage} /></div><MasteryBar value={item.M} label="Understanding" /></div>)}</div>
        <h3 className="eyebrow detail-history-title">RECENT ANSWERS</h3>
        <div className="history-list">{detail.events.map((event) => <div key={event.id}><span className={event.correct ? "history-result right" : "history-result wrong"}>{event.correct ? "Correct" : "Incorrect"}</span><span>{event.concept_id} · {event.kind}</span><time>{event.ts ? new Date(event.ts).toLocaleString() : ""}</time></div>)}</div>
      </section></div>}
    </div>
  );
}