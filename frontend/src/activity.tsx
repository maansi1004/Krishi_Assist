// "Activity": the farmer's past eligibility results (each can be re-opened exactly as it was
// decided) and a plain-language log of what they did in the app.
import React, { useEffect, useState } from 'react';
import { FIELD_LABELS, mx } from './matches';

type Lang = 'en' | 'hi' | 'hinglish';

const TXT: Record<Lang, Record<string, string>> = {
  en: {
    eyebrow: 'ACTIVITY', title: 'Your past results and activity', sub: 'Every eligibility check you ran is kept, so you can see exactly why you got a result.',
    tabResults: 'Past results', tabLog: 'Activity log', loading: 'Loading…', error: 'Could not load this page.', signIn: 'Please sign in to see your activity.', signInBtn: 'Sign in',
    emptyResults: 'No checks yet. Open a scheme and press Check eligibility.', emptyLog: 'Nothing recorded yet.',
    open: 'View', close: 'Close', checkedOn: 'Checked', rules: 'rules', data: 'scheme data',
    changed: 'The rules for this scheme were changed after this check. Run it again to get a result under the current rules.',
    profileUsed: 'Farm details used', criteria: 'Rule by rule', missing: 'Still needed', none: 'None', unverified: 'unverified', yes: 'Yes', no: 'No',
    answers: 'Your answers to scheme questions', privacy: 'This log shows what happened, not your personal details.'
  },
  hi: {
    eyebrow: 'गतिविधि', title: 'आपके पिछले नतीजे और गतिविधि', sub: 'आपकी हर पात्रता जांच सुरक्षित रहती है, ताकि आप देख सकें कि नतीजा क्यों आया।',
    tabResults: 'पिछले नतीजे', tabLog: 'गतिविधि लॉग', loading: 'लोड हो रहा है…', error: 'यह पेज लोड नहीं हो सका।', signIn: 'अपनी गतिविधि देखने के लिए साइन इन करें।', signInBtn: 'साइन इन',
    emptyResults: 'अभी कोई जांच नहीं हुई। कोई योजना खोलें और पात्रता जांचें दबाएं।', emptyLog: 'अभी कुछ दर्ज नहीं है।',
    open: 'देखें', close: 'बंद करें', checkedOn: 'जांच की गई', rules: 'नियम', data: 'योजना डेटा',
    changed: 'इस जांच के बाद इस योजना के नियम बदल गए हैं। मौजूदा नियमों के हिसाब से नतीजा पाने के लिए फिर से जांचें।',
    profileUsed: 'इस्तेमाल की गई फार्म जानकारी', criteria: 'नियम दर नियम', missing: 'अभी भी चाहिए', none: 'कुछ नहीं', unverified: 'असत्यापित', yes: 'हाँ', no: 'नहीं',
    answers: 'योजना के सवालों पर आपके जवाब', privacy: 'यह लॉग बताता है कि क्या हुआ, आपकी निजी जानकारी नहीं।'
  },
  hinglish: {
    eyebrow: 'ACTIVITY', title: 'Aapke pichhle results aur activity', sub: 'Aapki har eligibility check safe rehti hai, taaki aap dekh saken ki result kyon aaya.',
    tabResults: 'Pichhle results', tabLog: 'Activity log', loading: 'Load ho raha hai…', error: 'Ye page load nahi ho saka.', signIn: 'Apni activity dekhne ke liye sign in karein.', signInBtn: 'Sign in',
    emptyResults: 'Abhi koi check nahi hui. Koi scheme kholein aur Check eligibility dabayein.', emptyLog: 'Abhi kuch record nahi hai.',
    open: 'Dekhein', close: 'Band karein', checkedOn: 'Check hui', rules: 'rules', data: 'scheme data',
    changed: 'Is check ke baad is scheme ke rules badal gaye hain. Maujooda rules ke hisaab se result ke liye phir se check karein.',
    profileUsed: 'Istemaal ki gayi farm details', criteria: 'Rule dar rule', missing: 'Abhi bhi chahiye', none: 'Kuch nahi', unverified: 'unverified', yes: 'Haan', no: 'Nahi',
    answers: 'Scheme ke sawaalon par aapke jawab', privacy: 'Ye log batata hai ki kya hua, aapki personal details nahi.'
  }
};
const tr = (lang: Lang, key: string) => TXT[lang]?.[key] ?? TXT.en[key] ?? key;

// One sentence per kind of event. {a} {b} {c} are filled from the event details.
const EVENTS: Record<string, [string, string, string]> = {
  user_registered: ['You created your account', 'आपने अपना खाता बनाया', 'Aapne apna account banaya'],
  login_succeeded: ['You signed in', 'आपने साइन इन किया', 'Aapne sign in kiya'],
  login_failed: ['A sign-in attempt failed', 'एक साइन-इन कोशिश विफल रही', 'Ek sign-in koshish fail hui'],
  profile_created: ['You saved your farm profile ({a})', 'आपने अपनी फार्म प्रोफाइल सेव की ({a})', 'Aapne farm profile save ki ({a})'],
  profile_updated: ['You updated your farm profile ({a})', 'आपने अपनी फार्म प्रोफाइल अपडेट की ({a})', 'Aapne farm profile update ki ({a})'],
  evaluation_run: ['You checked {a}: {b}', 'आपने {a} जांची: {b}', 'Aapne {a} check ki: {b}'],
  application_created: ['You started tracking {a} ({b})', 'आपने {a} को ट्रैक करना शुरू किया ({b})', 'Aapne {a} ko track karna shuru kiya ({b})'],
  application_status_changed: ['{a}: {b} → {c}', '{a}: {b} → {c}', '{a}: {b} → {c}'],
  scheme_saved: ['You saved {a}', 'आपने {a} सेव की', 'Aapne {a} save ki'],
  scheme_unsaved: ['You removed {a} from saved schemes', 'आपने {a} को सेव की गई योजनाओं से हटाया', 'Aapne {a} ko saved schemes se hataya'],
  need_extracted: ['You described what you need', 'आपने अपनी ज़रूरत बताई', 'Aapne apni zaroorat batayi'],
};

const asUtc = (s: string) => (/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z');
const when = (s: string, lang: Lang) => { try { return new Date(asUtc(s)).toLocaleString(lang === 'en' ? 'en-IN' : 'hi-IN', { dateStyle: 'medium', timeStyle: 'short' }); } catch { return s; } };
const human = (field: string, lang: Lang) => FIELD_LABELS[lang][field] || field.replace(/_/g, ' ');

export function describeEvent(e: { event: string; payload: any }, lang: Lang, nameOf: (c: string, f: string) => string): string {
  const row = EVENTS[e.event];
  if (!row) return e.event.replace(/_/g, ' ');
  const p = e.payload || {};
  const code = p.scheme_code ? nameOf(p.scheme_code, p.scheme_code) : '';
  const vars: Record<string, string> = {
    a: code || (p.fields_changed ? (p.fields_changed as string[]).map(f => human(f, lang)).join(', ') || '—' : ''),
    b: p.status ? mx(lang, p.status) === p.status ? p.status : mx(lang, p.status) : (p.from ?? ''),
    c: p.to ?? '',
  };
  if (e.event === 'application_status_changed') { vars.b = p.from; vars.c = p.to; }
  return (row[lang === 'en' ? 0 : lang === 'hi' ? 1 : 2]).replace(/\{(\w)\}/g, (_, k) => vars[k] ?? '');
}

export function ActivityPage({ api, token, lang, nameOf, onLogin }: {
  api: string; token: string; lang: Lang; nameOf: (code: string, fallback: string) => string; onLogin: () => void;
}) {
  const [tab, setTab] = useState<'results' | 'log'>('results');
  const [history, setHistory] = useState<any[] | null>(null);
  const [log, setLog] = useState<any[] | null>(null);
  const [detail, setDetail] = useState<any | null>(null);
  const [error, setError] = useState('');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!token) return;
    setError('');
    fetch(`${api}/api/eligibility/history`, { headers }).then(async r => { if (!r.ok) throw new Error(); setHistory(await r.json()); }).catch(() => setError(tr(lang, 'error')));
    fetch(`${api}/api/audit?limit=100`, { headers }).then(async r => { if (!r.ok) throw new Error(); setLog(await r.json()); }).catch(() => setError(tr(lang, 'error')));
  }, [token]);

  const open = (id: number) => {
    fetch(`${api}/api/eligibility/history/${id}`, { headers }).then(async r => { if (!r.ok) throw new Error(); setDetail(await r.json()); }).catch(() => setError(tr(lang, 'error')));
  };

  const head = (
    <div className="pageIntro"><div>
      <p className="eyebrow dark">{tr(lang, 'eyebrow')}</p><h2>{tr(lang, 'title')}</h2><p>{tr(lang, 'sub')}</p>
    </div></div>
  );
  if (!token) return <section className="section page">{head}<p>{tr(lang, 'signIn')}</p><button className="primary" onClick={onLogin}>{tr(lang, 'signInBtn')}</button></section>;

  const snapshot = detail ? Object.entries(detail.profileSnapshot || {}).filter(([k, v]) => k !== 'extra_attributes' && v !== null && v !== '' && !(Array.isArray(v) && !v.length)) : [];
  const answers = detail ? Object.entries(detail.profileSnapshot?.extra_attributes || {}) : [];

  return (
    <section className="section page">{head}
      <div className="activityTabs">
        <button type="button" className={tab === 'results' ? 'active' : ''} onClick={() => setTab('results')}>{tr(lang, 'tabResults')}</button>
        <button type="button" className={tab === 'log' ? 'active' : ''} onClick={() => setTab('log')}>{tr(lang, 'tabLog')}</button>
      </div>
      {error && <p className="matchError">{error}</p>}

      {tab === 'results' && (history === null ? <p>{tr(lang, 'loading')}</p> : history.length === 0 ? <p>{tr(lang, 'emptyResults')}</p> : (
        <ul className="historyList">
          {history.map(h => (
            <li key={h.id} className="historyRow">
              <div>
                <b>{nameOf(h.schemeCode, h.schemeCode)}</b>
                <small>{tr(lang, 'checkedOn')} {when(h.createdAt, lang)} · {tr(lang, 'rules')} {h.ruleVersion || '—'} · {tr(lang, 'data')} {h.schemeVersion === 'unverified' ? tr(lang, 'unverified') : h.schemeVersion || '—'}</small>
              </div>
              <span className={`matchChip ${String(h.status).toLowerCase()}`}>{mx(lang, h.status)}</span>
              <button type="button" className="textBtn" onClick={() => open(h.id)}>{tr(lang, 'open')} →</button>
            </li>
          ))}
        </ul>
      ))}

      {tab === 'results' && detail && (
        <div className="historyDetail">
          <div className="historyDetailHead">
            <h3>{nameOf(detail.schemeCode, detail.schemeCode)} <span className={`matchChip ${String(detail.status).toLowerCase()}`}>{mx(lang, detail.status)}</span></h3>
            <button type="button" className="outline" onClick={() => setDetail(null)}>{tr(lang, 'close')}</button>
          </div>
          <p className="matchGroupDesc">{tr(lang, 'checkedOn')} {when(detail.createdAt, lang)}</p>
          {detail.rulesChangedSince && <p className="unverifiedNote">{tr(lang, 'changed')}</p>}
          <h4>{tr(lang, 'criteria')}</h4>
          <ul className="criteriaList">
            {(detail.criteria || []).map((c: any, i: number) => (
              <li key={i}><span className={`criterionDot ${String(c.result).toLowerCase()}`}></span><div><b>{c.criterion}</b><small>{c.explanation}</small></div></li>
            ))}
          </ul>
          <h4>{tr(lang, 'profileUsed')}</h4>
          <dl className="snapshot">
            {snapshot.map(([k, v]) => <React.Fragment key={k}><dt>{human(k, lang)}</dt><dd>{String(v)}</dd></React.Fragment>)}
          </dl>
          {answers.length > 0 && <>
            <h4>{tr(lang, 'answers')}</h4>
            <dl className="snapshot">
              {answers.map(([k, v]) => <React.Fragment key={k}><dt>{k.replace(/_/g, ' ')}</dt><dd>{v === true ? tr(lang, 'yes') : v === false ? tr(lang, 'no') : String(v)}</dd></React.Fragment>)}
            </dl>
          </>}
          {(detail.missingRequirements || []).length > 0 && <p className="matchGroupDesc"><b>{tr(lang, 'missing')}:</b> {detail.missingRequirements.map((m: string) => m.replace(/_/g, ' ')).join(', ')}</p>}
        </div>
      )}

      {tab === 'log' && (log === null ? <p>{tr(lang, 'loading')}</p> : log.length === 0 ? <p>{tr(lang, 'emptyLog')}</p> : (
        <>
          <ul className="logList">
            {log.map(e => <li key={e.id}><span>{describeEvent(e, lang, nameOf)}</span><small>{when(e.createdAt, lang)}</small></li>)}
          </ul>
          <p className="sourceNote">{tr(lang, 'privacy')}</p>
        </>
      ))}
    </section>
  );
}
