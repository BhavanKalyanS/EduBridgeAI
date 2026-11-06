import { Languages } from "lucide-react";
import { useTranslation } from "react-i18next";

const languages = [
  ["en", "English"], ["ta", "தமிழ்"], ["ml", "മലയാളം"], ["kn", "ಕನ್ನಡ"], ["te", "తెలుగు"],
];

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  return (
    <label className="language-switcher">
      <Languages size={16} aria-hidden="true" />
      <span className="sr-only">{t("language")}</span>
      <select value={i18n.language} onChange={(event) => i18n.changeLanguage(event.target.value)} aria-label={t("language")}>
        {languages.map(([code, name]) => <option value={code} key={code}>{name}</option>)}
      </select>
    </label>
  );
}