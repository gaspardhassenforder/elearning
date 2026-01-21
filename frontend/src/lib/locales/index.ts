import { enUS } from './en-US';
import { frFR } from './fr-FR';

export const resources = {
  'en-US': { translation: enUS },
  'fr-FR': { translation: frFR },
} as const;

export type TranslationKeys = typeof enUS;

export type LanguageCode = 'en-US' | 'fr-FR';

export type Language = {
  code: LanguageCode;
  label: string;
};

export const languages: Language[] = [
  { code: 'en-US', label: 'English' },
  { code: 'fr-FR', label: 'Français' },
];

export { enUS, frFR };
