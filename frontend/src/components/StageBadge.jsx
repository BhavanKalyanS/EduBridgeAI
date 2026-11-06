const stageNames = ["Regional", "Keyword bridge", "Bilingual", "English + help", "English"];

export default function StageBadge({ stage = 0 }) {
  const safeStage = Math.max(0, Math.min(4, Number(stage)));
  return (
    <span className={`stage-badge stage-${safeStage}`}>
      <span className="stage-dot" />
      Stage {safeStage} <span className="stage-name">{stageNames[safeStage]}</span>
    </span>
  );
}