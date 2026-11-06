import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import ta from "./locales/ta.json";
import ml from "./locales/ml.json";
import kn from "./locales/kn.json";
import te from "./locales/te.json";

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, ta: { translation: ta }, ml: { translation: ml }, kn: { translation: kn }, te: { translation: te } },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;