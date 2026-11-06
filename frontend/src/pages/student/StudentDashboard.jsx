import { ArrowRight, BookOpenText, Check, ChevronRight, RotateCcw, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api, { errorMessage } from "../../api/client";
import MasteryBar from "../../components/MasteryBar";
import StageBadge from "../../components/StageBadge";
import TextbookPdfViewer from "../../components/TextbookPdfViewer";

export default function StudentDashboard() {
  const { t } = useTranslation();
  const [concepts, setConcepts] = useState([]);
  const [revision, setRevision] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [lesson, setLesson] = useState(null);
  const [sourcePdf, setSourcePdf] = useState(null);
  const [sourcePdfLoading, setSourcePdfLoading] = useState(false);
  const [sourcePdfFailed, setSourcePdfFailed] = useState(false);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([api.get("/concepts"), api.get("/learn/revision")])
      .then(([conceptResponse, revisionResponse]) => {
        if (!active) return;
        const items = conceptResponse.data.concepts || [];
        setConcepts(items);
        setRevision(revisionResponse.data.concepts || []);
        setSelectedSubject(items[0]?.subject || "");
        setSelectedId(items[0]?.concept_id || "");
      })
      .catch((requestError) => active && setError(errorMessage(requestError)))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selectedId) return undefined;
    let active = true;
    api.get(`/learn/${selectedId}`)
      .then(({ data }) => {
        if (active) {
          setSourcePdfLoading(Boolean(data.textbook_source));
          setLesson(data);
          setError("");
        }
      })
      .catch((requestError) => active && setError(errorMessage(requestError)))
    return () => { active = false; };
  }, [selectedId]);

  useEffect(() => {
    if (!lesson?.textbook_source || lesson.concept_id !== selectedId) return undefined;

    let active = true;
    api.get(`/learn/${selectedId}/source.pdf`, { responseType: "blob" })
      .then(({ data }) => {
        if (active) setSourcePdf(data);
      })
      .catch((requestError) => {
        if (active) {
          setSourcePdfFailed(true);
          setError(errorMessage(requestError));
        }
      })
      .finally(() => active && setSourcePdfLoading(false));

    return () => { active = false; };
  }, [lesson?.concept_id, lesson?.textbook_source, selectedId]);

  function selectConcept(conceptId) {
    setSelectedSubject(concepts.find((item) => item.concept_id === conceptId)?.subject || "");
    setLesson(null);
    setSourcePdf(null);
    setSourcePdfLoading(false);
    setSourcePdfFailed(false);
    setFeedback(null);
    setSelectedOption("");
    setQuestionIndex(0);
    setSelectedId(conceptId);
  }

  async function submitAnswer() {
    const question = lesson?.quiz?.[questionIndex];
    if (!question || !selectedOption) return;
    setError("");
    try {
      const { data } = await api.post("/learn/answer", {
        event_id: crypto.randomUUID(),
        concept_id: lesson.concept_id,
        stage: lesson.stage,
        q_id: question.q_id,
        selected_option: selectedOption,
        time_ms: 0,
      });
      setFeedback(data);
      setConcepts((items) => items.map((item) => item.concept_id === lesson.concept_id ? { ...item, M: data.M, L: data.L, stage: data.stage } : item));
      if (data.stage_changed) {
        const updatedLesson = await api.get(`/learn/${lesson.concept_id}`);
        setLesson(updatedLesson.data);
        setQuestionIndex(0);
      } else {
        setQuestionIndex((index) => index + 1);
      }
      setSelectedOption("");
    } catch (requestError) {
      setError(errorMessage(requestError));
    }
  }

  async function loadSourcePdf() {
    setSourcePdfLoading(true);
    setError("");
    try {
      const { data } = await api.get(`/learn/${selectedId}/source.pdf`, { responseType: "blob" });
      setSourcePdf(data);
      setSourcePdfFailed(false);
    } catch (requestError) {
      setSourcePdfFailed(true);
      setError(errorMessage(requestError));
    } finally {
      setSourcePdfLoading(false);
    }
  }

  const selectedConcept = concepts.find((item) => item.concept_id === selectedId);
  const availableSubjects = [...new Set(concepts.map((item) => item.subject))].sort();
  const visibleConcepts = concepts.filter((item) => item.subject === selectedSubject);
  const lessonLoading = Boolean(selectedId) && (!lesson || lesson.concept_id !== selectedId);
  const activeQuestion = lesson?.quiz?.[questionIndex];
  const completed = Boolean(lesson?.quiz?.length) && questionIndex >= lesson.quiz.length;
  const completedCount = concepts.filter((item) => item.stage >= 4).length;
  const inProgressCount = concepts.filter((item) => item.started && item.stage < 4).length;

  if (loading) return <div className="loading-state">{t("loading")}</div>;

  return (
    <div className="dashboard-page student-page">
      <section className="welcome-band">
        <div>
          <div className="eyebrow"><span /> YOUR LEARNING PATH</div>
          <h1>One concept at a time.</h1>
          <p>Start where the idea makes sense. English support grows with your understanding.</p>
        </div>
        <div className="welcome-number"><span>{concepts.length.toString().padStart(2, "0")}</span><small>CONCEPTS<br />IN YOUR PATH</small></div>
      </section>

      <div className="metric-strip">
        <div className="metric-item"><span className="metric-mark mark-teal"><BookOpenText size={17} /></span><div><strong>{concepts.length}</strong><small>Concepts</small></div></div>
        <div className="metric-item"><span className="metric-mark mark-coral"><Sparkles size={17} /></span><div><strong>{inProgressCount}</strong><small>In progress</small></div></div>
        <div className="metric-item"><span className="metric-mark mark-lime"><Check size={17} /></span><div><strong>{completedCount}</strong><small>Completed</small></div></div>
        <div className="metric-note"><span className="note-line" /> {t("stageNote")}</div>
      </div>

      {error && <div className="notice error-notice" role="alert">{error}</div>}
      {concepts.length === 0 ? <div className="empty-state"><BookOpenText size={24} /><p>{t("noConcepts")}</p></div> : (
        <div className="learning-layout">
          <section className="concept-panel">
            <div className="section-heading"><div><div className="eyebrow">GRADE 10 · {selectedSubject.toUpperCase()}</div><h2>Your concepts</h2></div><label className="subject-filter"><span className="sr-only">Subject</span><select aria-label="Subject" value={selectedSubject} onChange={(event) => { const subject = event.target.value; setSelectedSubject(subject); const firstConcept = concepts.find((item) => item.subject === subject); if (firstConcept) selectConcept(firstConcept.concept_id); }}>{availableSubjects.map((subject) => <option value={subject} key={subject}>{subject}</option>)}</select></label></div>
            <div className="concept-list">
              {visibleConcepts.map((concept, index) => (
                <button className={`concept-row ${selectedId === concept.concept_id ? "selected" : ""}`} type="button" onClick={() => selectConcept(concept.concept_id)} key={concept.concept_id}>
                  <span className="concept-index">{String(index + 1).padStart(2, "0")}</span>
                  <span className="concept-main"><strong>{concept.title || concept.concept_id}</strong><small>{concept.chapter} <span>·</span> {concept.lesson}</small><span className="concept-progress"><span style={{ width: `${Math.round((concept.M || 0) * 100)}%` }} /></span></span>
                  <StageBadge stage={concept.stage} />
                  <ChevronRight className="concept-chevron" size={17} />
                </button>
              ))}
            </div>
            {revision.length > 0 && <div className="revision-strip"><RotateCcw size={16} /><span><strong>{revision.length} concepts</strong> are ready for a little more practice.</span></div>}
          </section>

          <section className="lesson-panel">
            {lessonLoading ? <div className="loading-state">Opening lesson...</div> : lesson ? (
              <>
                <div className="lesson-kicker"><span>LESSON</span><StageBadge stage={lesson.stage} /></div>
                <h2>{lesson.title || selectedConcept?.title || selectedId}</h2>
                <p className="lesson-meta">{selectedConcept?.subject} <span>·</span> {selectedConcept?.chapter}</p>
                {lesson.textbook_source && (
                  <div className="textbook-source-note">
                    Original textbook PDF · English · {lesson.source_page_count} pages.
                    {sourcePdfFailed && !sourcePdf && <button type="button" onClick={loadSourcePdf} disabled={sourcePdfLoading}>{sourcePdfLoading ? "Loading PDF..." : "Retry loading PDF"}</button>}
                  </div>
                )}
                {lesson.textbook_source
                  ? sourcePdf
                    ? <TextbookPdfViewer key={lesson.concept_id} file={sourcePdf} title={lesson.title} />
                    : sourcePdfFailed
                      ? <div className="textbook-pdf-loading" role="status">The PDF could not be loaded.</div>
                      : <div className="textbook-pdf-loading" role="status">{sourcePdfLoading || !sourcePdf ? "Loading textbook PDF..." : "The PDF could not be loaded."}</div>
                  : <div className="lesson-content"><p>{lesson.content}</p></div>}
                {lesson.keywords?.length > 0 && (
                  <div className="keyword-area"><div className="eyebrow">KEY WORDS</div><div className="keyword-list">{lesson.keywords.map((keyword, index) => <div className="keyword-item" key={`${keyword.en}-${index}`}><strong>{keyword.en}</strong><span>{keyword.regional}</span></div>)}</div></div>
                )}
                <div className="mastery-pair">
                  <MasteryBar value={selectedConcept?.M} label={t("understanding")} tone="teal" />
                  <MasteryBar value={selectedConcept?.L} label={t("englishWords")} tone="coral" />
                </div>
                <div className="stage-explanation"><span className="stage-explanation-mark">i</span>{t("stageNote")}</div>
                <div className="quiz-area">
                  <div className="quiz-head"><span className="eyebrow">QUICK CHECK</span>{lesson.quiz?.length > 0 && <span className="quiz-count">{completed ? lesson.quiz.length : Math.min(questionIndex + 1, lesson.quiz.length)} / {lesson.quiz.length}</span>}</div>
                  {activeQuestion ? (
                    <div className="quiz-question">
                      <h3>{activeQuestion.question}</h3>
                      <div className="quiz-options">
                        {activeQuestion.options.map((option) => (
                          <button key={option} type="button" className={`quiz-option ${selectedOption === option ? "chosen" : ""}`} onClick={() => setSelectedOption(option)}>
                            <span className="option-radio" />{option}
                          </button>
                        ))}
                      </div>
                      {feedback && <div className={`answer-feedback ${feedback.correct ? "correct" : "incorrect"}`} role="status">{feedback.correct ? "That’s right. Keep going." : "Not quite. Your progress is saved; give it another look."}{feedback.stage_changed && <strong> You moved to Stage {feedback.stage}.</strong>}{feedback.vocab_flag && <strong> {t("needsSupport")}.</strong>}</div>}
                      <button className="primary-button quiz-submit" type="button" disabled={!selectedOption} onClick={submitAnswer}>{t("checkAnswer")} <ArrowRight size={17} /></button>
                    </div>
                  ) : completed ? (
                    <div className="quiz-complete"><span className="complete-check"><Check size={20} /></span><strong>Practice complete</strong><p>Your answers have updated your concept progress.</p>{feedback && <div className={`answer-feedback ${feedback.correct ? "correct" : "incorrect"}`} role="status">{feedback.correct ? "That’s right. Keep going." : "Not quite. Your progress is saved; give it another look."}{feedback.vocab_flag && <strong> {t("needsSupport")}.</strong>}</div>}<button className="text-button" type="button" onClick={() => { setQuestionIndex(0); setFeedback(null); }}>{t("retry")} <ArrowRight size={15} /></button></div>
                  ) : <p className="muted-copy">No quiz questions are available for this concept yet.</p>}
                </div>
              </>
            ) : <div className="empty-state">Choose a concept to begin.</div>}
          </section>
        </div>
      )}
    </div>
  );
}