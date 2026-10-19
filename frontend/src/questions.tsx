// Helpers for the profile dropdowns and the "answer these questions" form.
// Kept in its own file so main.tsx does not grow even bigger.
import React from 'react';

type Lang = 'en' | 'hi' | 'hinglish';
export type Option = { value: string; label: string };

/* ---------- Dropdown options for the profile form ---------- */
// The values below are exactly what the scheme rules compare against.
const states = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana',
  'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
  'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Andaman and Nicobar Islands', 'Chandigarh',
  'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
];

export const PROFILE_OPTIONS: Record<string, Option[]> = {
  state: states.map(s => ({ value: s, label: s })),
  farmer_type: [
    { value: 'farmer', label: 'Farmer (owns land)' },
    { value: 'tenant_farmer', label: 'Tenant farmer' },
    { value: 'sharecropper', label: 'Sharecropper' },
    { value: 'farmer_family_member', label: 'Farmer family member' }
  ],
  gender: [
    { value: 'Male', label: 'Male' },
    { value: 'Female', label: 'Female' },
    { value: 'Other', label: 'Other' }
  ],
  social_category: [
    { value: 'General', label: 'General' },
    { value: 'OBC', label: 'OBC' },
    { value: 'SC', label: 'SC' },
    { value: 'ST', label: 'ST' }
  ],
  bank_account_status: [
    { value: 'active', label: 'Active bank account' },
    { value: 'inactive', label: 'Inactive bank account' },
    { value: 'none', label: 'No bank account' }
  ]
};

/* ---------- Answer lists for scheme-specific questions ---------- */
const ANSWER_OPTIONS: Record<string, Option[]> = {
  groundwater_category: [
    { value: 'safe', label: 'Safe' },
    { value: 'semi_critical', label: 'Semi-critical' },
    { value: 'critical', label: 'Critical' },
    { value: 'over_exploited', label: 'Over-exploited' }
  ],
  project_type: [
    { value: 'collective_irrigation', label: 'Collective irrigation project' },
    { value: 'individual_groundwater_irrigation', label: 'Individual groundwater irrigation' },
    { value: 'other', label: 'Something else' }
  ],
  aromatic_land_access: [
    { value: 'owned', label: 'I own the land' },
    { value: 'lease_10_years_plus', label: 'Leased for 10+ years' },
    { value: 'lease_under_10_years', label: 'Leased for less than 10 years' },
    { value: 'none', label: 'No land access' }
  ]
};

/* ---------- Small translations for the new screens ---------- */
const TXT: Record<Lang, Record<string, string>> = {
  en: {
    title: 'Answer these to get a clear result',
    sub: 'We could not decide these points from your profile. Your answers are saved to your farm profile.',
    yes: 'Yes', no: 'No', choose: 'Choose…', recheck: 'Check again', checking: 'Checking…',
    profileMissing: 'Also complete these in My Farm profile:', openProfile: 'Open My Farm',
    unverified: 'This scheme’s data is still being verified. Please confirm the rules with the official source before applying.',
    notProvided: 'Not provided'
  },
  hi: {
    title: 'साफ़ नतीजे के लिए ये सवाल भरें',
    sub: 'आपकी प्रोफाइल से ये बातें तय नहीं हो सकीं। आपके जवाब आपकी फार्म प्रोफाइल में सेव होंगे।',
    yes: 'हाँ', no: 'नहीं', choose: 'चुनें…', recheck: 'फिर से जांचें', checking: 'जांच हो रही है…',
    profileMissing: 'ये जानकारी My Farm प्रोफाइल में भी भरें:', openProfile: 'My Farm खोलें',
    unverified: 'इस योजना का डेटा अभी सत्यापित हो रहा है। आवेदन से पहले आधिकारिक स्रोत से नियम जांच लें।',
    notProvided: 'नहीं दिया'
  },
  hinglish: {
    title: 'Clear result ke liye ye sawaal bharein',
    sub: 'Aapki profile se ye baatein tay nahi ho saki. Aapke jawab farm profile mein save honge.',
    yes: 'Haan', no: 'Nahi', choose: 'Chunein…', recheck: 'Phir se check karein', checking: 'Check ho raha hai…',
    profileMissing: 'Ye info My Farm profile mein bhi bharein:', openProfile: 'My Farm kholein',
    unverified: 'Is scheme ka data abhi verify ho raha hai. Apply karne se pehle official source se rules confirm karein.',
    notProvided: 'Nahi diya'
  }
};
export const tx = (lang: Lang, key: string) => TXT[lang]?.[key] ?? TXT.en[key] ?? key;

/* ---------- Dropdown used on the profile page ---------- */
export function ProfileSelect({ field, label, value, onChange, lang }: {
  field: string; label: string; value: string | undefined; onChange: (v: string | undefined) => void; lang: Lang;
}) {
  const options = PROFILE_OPTIONS[field] || [];
  const known = options.some(o => o.value === value);
  return (
    <label>{label}
      <select value={value ?? ''} onChange={e => onChange(e.target.value === '' ? undefined : e.target.value)}>
        <option value="">{tx(lang, 'notProvided')}</option>
        {/* An older saved value (for example typed by hand) stays visible instead of vanishing. */}
        {value && !known && <option value={value}>{value}</option>}
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}

/* ---------- The questions form ---------- */
type Criterion = { field: string; source?: string; operator?: string; expected?: any; result: string; criterion?: string };

export function QuestionsForm({ result, extra, onAnswer, onRecheck, busy, onOpenProfile, lang }: {
  result: { criteria?: Criterion[]; exclusions?: Criterion[]; verificationCriteria?: Criterion[]; unverifiedScheme?: boolean };
  extra: Record<string, unknown>;
  onAnswer: (field: string, value: unknown) => void;
  onRecheck: () => void;
  busy: boolean;
  onOpenProfile: () => void;
  lang: Lang;
}) {
  const all = [...(result.criteria || []), ...(result.exclusions || []), ...(result.verificationCriteria || [])];
  const unknown = all.filter(c => c.result === 'UNKNOWN');
  const seen = new Set<string>();
  const questions = unknown.filter(c => c.source === 'extra_attributes' && !seen.has(c.field) && seen.add(c.field));
  const profileFields = [...new Set(unknown.filter(c => c.source !== 'extra_attributes').map(c => c.field))];

  if (!questions.length && !profileFields.length) return null;

  const numeric = (c: Criterion) => ['gt', 'gte', 'lt', 'lte'].includes(c.operator || '');
  const input = (c: Criterion) => {
    const current = extra[c.field];
    if (typeof c.expected === 'boolean') {
      return (
        <select value={current === undefined ? '' : String(current)}
          onChange={e => onAnswer(c.field, e.target.value === '' ? undefined : e.target.value === 'true')}>
          <option value="">{tx(lang, 'choose')}</option>
          <option value="true">{tx(lang, 'yes')}</option>
          <option value="false">{tx(lang, 'no')}</option>
        </select>
      );
    }
    if (numeric(c)) {
      return (
        <input type="number" min="0" value={current === undefined ? '' : String(current)}
          onChange={e => onAnswer(c.field, e.target.value === '' ? undefined : Number(e.target.value))} />
      );
    }
    const options: Option[] = ANSWER_OPTIONS[c.field]
      || (Array.isArray(c.expected) ? c.expected.map((v: any) => ({ value: String(v), label: String(v).replace(/_/g, ' ') })) : []);
    if (options.length) {
      return (
        <select value={current === undefined ? '' : String(current)}
          onChange={e => onAnswer(c.field, e.target.value === '' ? undefined : e.target.value)}>
          <option value="">{tx(lang, 'choose')}</option>
          {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      );
    }
    return <input type="text" value={current === undefined ? '' : String(current)}
      onChange={e => onAnswer(c.field, e.target.value === '' ? undefined : e.target.value)} />;
  };

  return (
    <div className="questionsPanel">
      {questions.length > 0 && <>
        <h4>{tx(lang, 'title')}</h4>
        <p className="questionsSub">{tx(lang, 'sub')}</p>
        <div className="questionsList">
          {questions.map(c => (
            <label key={c.field}>
              <span>{c.criterion || c.field.replace(/_/g, ' ')}</span>
              {input(c)}
            </label>
          ))}
        </div>
        <button type="button" className="primary small" onClick={onRecheck} disabled={busy}>
          {busy ? tx(lang, 'checking') : tx(lang, 'recheck')}
        </button>
      </>}
      {profileFields.length > 0 && (
        <p className="questionsProfile">
          {tx(lang, 'profileMissing')} <b>{profileFields.map(f => f.replace(/_/g, ' ')).join(', ')}</b>{' '}
          <button type="button" className="textBtn" onClick={onOpenProfile}>{tx(lang, 'openProfile')} →</button>
        </p>
      )}
    </div>
  );
}
