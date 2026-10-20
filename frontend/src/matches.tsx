// "My Matches": every scheme checked against the saved farm profile, grouped by result,
// plus the "profile complete?" banner. The decisions come from the backend rule engine;
// this file only shows them.
import React, { useEffect, useState } from 'react';

type Lang = 'en' | 'hi' | 'hinglish';
export type Completeness = { total: number; filled: number; percent: number; complete: boolean; missing: { field: string; label: string }[] };
type Match = {
  schemeCode: string; name: string; state?: string | null; category?: string | null; status: string;
  unverifiedScheme: boolean; passed: number; total: number; reason?: string | null;
  questionsToAnswer: number; profileFieldsMissing: string[]; otherState: boolean;
};
type MatchesResponse = { profileUsed: boolean; profileCompleteness: Completeness; schemeCount: number; counts: Record<string, number>; groups: Record<string, Match[]> };

const TXT: Record<Lang, Record<string, string>> = {
  en: {
    navLabel: 'My Matches', title: 'Schemes matched to your farm',
    sub: 'Every scheme is checked against your saved farm profile by the rule engine. Open a scheme to see the full reasons.',
    refresh: 'Refresh', loading: 'Checking all schemes…', error: 'Could not load your matches.',
    signIn: 'Please sign in to see schemes matched to your farm.', signInBtn: 'Sign in',
    noProfile: 'Save your farm profile first, so we can check the schemes for you.', openProfile: 'Open My Farm',
    completeTitle: 'Your farm profile is {p}% complete', completeHint: 'Adding these gives clearer results:',
    completeDone: 'Your farm profile is complete.', seeMatches: 'See my matches →',
    ELIGIBLE: 'Eligible', ALMOST_ELIGIBLE: 'Almost eligible', VERIFICATION_REQUIRED: 'Needs verification', NOT_ELIGIBLE: 'Not eligible',
    dELIGIBLE: 'Your profile meets the rules we could check.',
    dALMOST_ELIGIBLE: 'You meet most rules. A few answers or documents are still needed.',
    dVERIFICATION_REQUIRED: 'We need more information or an official check before we can say.',
    dNOT_ELIGIBLE: 'A rule in your profile does not match.',
    rulesMet: '{a} of {b} rules met', answers: '{n} answers needed', unverified: 'Unverified data', otherState: 'Another state',
    view: 'View details →', unverifiedSection: 'Schemes with unverified data ({n})', notEligibleSection: 'Not eligible ({n})',
    note: 'Matches come from the rule engine, not from AI. Always confirm with the official source before applying.'
  },
  hi: {
    navLabel: 'मेरी योजनाएं', title: 'आपके खेत के लिए मिलती योजनाएं',
    sub: 'हर योजना को नियम इंजन आपकी सेव फार्म प्रोफाइल से जांचता है। पूरी वजह देखने के लिए योजना खोलें।',
    refresh: 'फिर से जांचें', loading: 'सभी योजनाएं जांची जा रही हैं…', error: 'आपकी योजनाएं लोड नहीं हो सकीं।',
    signIn: 'अपने खेत के लिए मिलती योजनाएं देखने के लिए साइन इन करें।', signInBtn: 'साइन इन',
    noProfile: 'पहले अपनी फार्म प्रोफाइल सेव करें, ताकि हम योजनाएं जांच सकें।', openProfile: 'My Farm खोलें',
    completeTitle: 'आपकी फार्म प्रोफाइल {p}% पूरी है', completeHint: 'ये जानकारी जोड़ने से नतीजे साफ़ होंगे:',
    completeDone: 'आपकी फार्म प्रोफाइल पूरी है।', seeMatches: 'मेरी योजनाएं देखें →',
    ELIGIBLE: 'पात्र', ALMOST_ELIGIBLE: 'लगभग पात्र', VERIFICATION_REQUIRED: 'सत्यापन आवश्यक', NOT_ELIGIBLE: 'पात्र नहीं',
    dELIGIBLE: 'आपकी प्रोफाइल उन नियमों पर खरी उतरती है जिन्हें हम जांच सके।',
    dALMOST_ELIGIBLE: 'आप ज़्यादातर नियम पूरे करते हैं। कुछ जवाब या दस्तावेज़ बाकी हैं।',
    dVERIFICATION_REQUIRED: 'कुछ कहने से पहले हमें और जानकारी या आधिकारिक जांच चाहिए।',
    dNOT_ELIGIBLE: 'आपकी प्रोफाइल का कोई नियम मेल नहीं खाता।',
    rulesMet: '{b} में से {a} नियम पूरे', answers: '{n} जवाब चाहिए', unverified: 'असत्यापित डेटा', otherState: 'दूसरा राज्य',
    view: 'विवरण देखें →', unverifiedSection: 'असत्यापित डेटा वाली योजनाएं ({n})', notEligibleSection: 'पात्र नहीं ({n})',
    note: 'ये नतीजे नियम इंजन से आते हैं, AI से नहीं। आवेदन से पहले आधिकारिक स्रोत से ज़रूर जांचें।'
  },
  hinglish: {
    navLabel: 'Meri Matches', title: 'Aapke khet ke liye matching schemes',
    sub: 'Har scheme ko rule engine aapki saved farm profile se check karta hai. Poori wajah dekhne ke liye scheme kholein.',
    refresh: 'Phir se check karein', loading: 'Sabhi schemes check ho rahi hain…', error: 'Aapki matches load nahi ho saki.',
    signIn: 'Apne khet ke liye matching schemes dekhne ke liye sign in karein.', signInBtn: 'Sign in',
    noProfile: 'Pehle apni farm profile save karein, taaki hum schemes check kar saken.', openProfile: 'My Farm kholein',
    completeTitle: 'Aapki farm profile {p}% poori hai', completeHint: 'Ye info jodne se result saaf aayega:',
    completeDone: 'Aapki farm profile poori hai.', seeMatches: 'Meri matches dekhein →',
    ELIGIBLE: 'Eligible', ALMOST_ELIGIBLE: 'Almost eligible', VERIFICATION_REQUIRED: 'Verification zaroori', NOT_ELIGIBLE: 'Eligible nahi',
    dELIGIBLE: 'Aapki profile un rules par khari utarti hai jo hum check kar sake.',
    dALMOST_ELIGIBLE: 'Aap zyadatar rules poore karte hain. Kuch jawab ya documents baaki hain.',
    dVERIFICATION_REQUIRED: 'Kuch kehne se pehle hamein aur info ya official check chahiye.',
    dNOT_ELIGIBLE: 'Aapki profile ka koi rule match nahi karta.',
    rulesMet: '{b} mein se {a} rules poore', answers: '{n} jawab chahiye', unverified: 'Unverified data', otherState: 'Dusra rajya',
    view: 'Details dekhein →', unverifiedSection: 'Unverified data wali schemes ({n})', notEligibleSection: 'Eligible nahi ({n})',
    note: 'Ye results rule engine se aate hain, AI se nahi. Apply karne se pehle official source se zaroor confirm karein.'
  }
};
const FIELD_LABELS: Record<Lang, Record<string, string>> = {
  en: {},
  hi: { state: 'राज्य', farmer_type: 'किसान का प्रकार', land_size_hectares: 'ज़मीन (हेक्टेयर)', age: 'उम्र', social_category: 'सामाजिक श्रेणी', primary_crop: 'मुख्य फसल', bank_account_status: 'बैंक खाता', kcc_holder: 'किसान क्रेडिट कार्ड', years_of_cultivation: 'खेती के साल' },
  hinglish: { state: 'Rajya', farmer_type: 'Kisan ka type', land_size_hectares: 'Zameen (hectare)', age: 'Umr', social_category: 'Social category', primary_crop: 'Main fasal', bank_account_status: 'Bank account', kcc_holder: 'Kisan Credit Card', years_of_cultivation: 'Kheti ke saal' }
};
export const mx = (lang: Lang, key: string) => TXT[lang]?.[key] ?? TXT.en[key] ?? key;
const fmt = (s: string, v: Record<string, string | number>) => s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? ''));

/* ---------- Profile complete? banner ---------- */
export function CompletenessBanner({ completeness, lang, onOpenProfile, onOpenMatches, showDone = false }: {
  completeness: Completeness | null; lang: Lang; onOpenProfile?: () => void; onOpenMatches?: () => void; showDone?: boolean;
}) {
  if (!completeness) return null;
  if (completeness.complete) {
    if (!showDone) return null;
    return (
      <div className="completeBanner done">
        <b>✓ {mx(lang, 'completeDone')}</b>
        {onOpenMatches && <button type="button" className="textBtn" onClick={onOpenMatches}>{mx(lang, 'seeMatches')}</button>}
      </div>
    );
  }
  const labels = completeness.missing.map(m => FIELD_LABELS[lang][m.field] || m.label).join(', ');
  return (
    <div className="completeBanner">
      <b>{fmt(mx(lang, 'completeTitle'), { p: completeness.percent })}</b>
      <div className="completeBar"><span style={{ width: `${completeness.percent}%` }} /></div>
      <p>{mx(lang, 'completeHint')} <b>{labels}</b></p>
      {onOpenProfile && <button type="button" className="textBtn" onClick={onOpenProfile}>{mx(lang, 'openProfile')} →</button>}
    </div>
  );
}

/* ---------- One scheme card ---------- */
function MatchCard({ m, lang, nameOf, onOpen }: { m: Match; lang: Lang; nameOf: (code: string, fallback: string) => string; onOpen: (code: string) => void }) {
  return (
    <div className="matchCard">
      <div className="matchTop">
        <div>
          <b className="matchName">{nameOf(m.schemeCode, m.name)}</b>
          <small>{m.schemeCode} · {m.state || 'India'}</small>
        </div>
        <span className={`matchChip ${m.status.toLowerCase()}`}>{mx(lang, m.status)}</span>
      </div>
      <p className="matchMeta">
        {m.total > 0 && <span>{fmt(mx(lang, 'rulesMet'), { a: m.passed, b: m.total })}</span>}
        {m.questionsToAnswer > 0 && <span>{fmt(mx(lang, 'answers'), { n: m.questionsToAnswer })}</span>}
        {m.unverifiedScheme && <span className="tagWarn">{mx(lang, 'unverified')}</span>}
        {m.otherState && <span className="tagMuted">{mx(lang, 'otherState')}</span>}
      </p>
      {m.reason && <p className="matchReason">{m.reason}</p>}
      <button type="button" className="textBtn" onClick={() => onOpen(m.schemeCode)}>{mx(lang, 'view')}</button>
    </div>
  );
}

/* ---------- The page ---------- */
export function MatchesPage({ api, token, lang, savedTick, nameOf, onOpenScheme, onOpenProfile, onLogin }: {
  api: string; token: string; lang: Lang; savedTick: number;
  nameOf: (code: string, fallback: string) => string;
  onOpenScheme: (code: string) => void; onOpenProfile: () => void; onLogin: () => void;
}) {
  const [data, setData] = useState<MatchesResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = () => {
    if (!token) return;
    setBusy(true); setError('');
    fetch(`${api}/api/matches`, { headers: { Authorization: `Bearer ${token}` } })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || mx(lang, 'error')); setData(d); })
      .catch(e => setError(e.message || mx(lang, 'error')))
      .finally(() => setBusy(false));
  };
  useEffect(load, [token, savedTick]);

  const head = (
    <div className="pageIntro">
      <div>
        <p className="eyebrow dark">{mx(lang, 'navLabel').toUpperCase()}</p>
        <h2>{mx(lang, 'title')}</h2>
        <p>{mx(lang, 'sub')}</p>
      </div>
      {token && <button type="button" className="outline" onClick={load} disabled={busy}>{busy ? mx(lang, 'loading') : mx(lang, 'refresh')}</button>}
    </div>
  );

  if (!token) return <section className="section page">{head}<p>{mx(lang, 'signIn')}</p><button className="primary" onClick={onLogin}>{mx(lang, 'signInBtn')}</button></section>;
  if (error) return <section className="section page">{head}<p className="matchError">{error}</p></section>;
  if (!data) return <section className="section page">{head}<p>{mx(lang, 'loading')}</p></section>;
  if (!data.profileUsed) return (
    <section className="section page">{head}
      <p>{mx(lang, 'noProfile')}</p>
      <button className="primary" onClick={onOpenProfile}>{mx(lang, 'openProfile')}</button>
    </section>
  );

  const card = (m: Match) => <MatchCard key={m.schemeCode} m={m} lang={lang} nameOf={nameOf} onOpen={onOpenScheme} />;
  const order = ['ELIGIBLE', 'ALMOST_ELIGIBLE', 'VERIFICATION_REQUIRED', 'NOT_ELIGIBLE'];

  return (
    <section className="section page">
      {head}
      <CompletenessBanner completeness={data.profileCompleteness} lang={lang} onOpenProfile={onOpenProfile} />
      <div className="matchCounts">
        {order.map(s => <span key={s} className={`matchChip ${s.toLowerCase()}`}>{mx(lang, s)}: {data.counts[s] ?? 0}</span>)}
      </div>

      {order.map(status => {
        const items = data.groups[status] || [];
        if (!items.length) return null;
        // "Not eligible" and schemes whose own data is unverified are tucked away so the
        // useful results stay on top.
        const shown = status === 'VERIFICATION_REQUIRED' ? items.filter(i => !i.unverifiedScheme) : status === 'NOT_ELIGIBLE' ? [] : items;
        const tucked = status === 'VERIFICATION_REQUIRED' ? items.filter(i => i.unverifiedScheme) : status === 'NOT_ELIGIBLE' ? items : [];
        return (
          <div key={status} className="matchGroup">
            <h3>{mx(lang, status)} <small>({items.length})</small></h3>
            <p className="matchGroupDesc">{mx(lang, 'd' + status)}</p>
            {shown.length > 0 && <div className="matchGrid">{shown.map(card)}</div>}
            {tucked.length > 0 && (
              <details className="matchMore">
                <summary>{fmt(mx(lang, status === 'NOT_ELIGIBLE' ? 'notEligibleSection' : 'unverifiedSection'), { n: tucked.length })}</summary>
                <div className="matchGrid">{tucked.map(card)}</div>
              </details>
            )}
          </div>
        );
      })}
      <p className="sourceNote">{mx(lang, 'note')}</p>
    </section>
  );
}
