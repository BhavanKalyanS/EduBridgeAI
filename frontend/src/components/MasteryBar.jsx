export default function MasteryBar({ value = 0, label, tone = "teal" }) {
  const percent = Math.round(Math.max(0, Math.min(1, Number(value))) * 100);
  return (
    <div className="mastery-meter">
      <div className="meter-label"><span>{label}</span><strong>{percent}%</strong></div>
      <div className="meter-track" role="progressbar" aria-label={label} aria-valuenow={percent} aria-valuemin="0" aria-valuemax="100">
        <span className={`meter-fill ${tone}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}