// "Describe what you need": the farmer writes a sentence, we SUGGEST structured details,
// the farmer confirms or corrects them, and only then are the schemes checked.
// Nothing is checked or saved before the confirm step, and the suggestions never decide eligibility.
import React, { useEffect, useState } from 'react';
import { PROFILE_OPTIONS } from './questions';
import { MatchResults, type MatchesResponse } from './matches';

type Lang = 'en' | 'hi' | 'hinglish';
type Extraction = {
  text: string; topics: { id: string; label: string }[]; notes: string[]; usedAI: boolean;
  fields: { field: string; value: any; label: string; evidence: string; source: string }[];
};
const KEY_FIELDS = ['state', 'farmer_type', 'land_size_hectares', 'age', 'social_category', 'gender', 'primary_crop'] as const;
const SELECT_FIELDS = ['state', 'farmer_type', 'social_category', 'gender'];
const NUMBER_FIELDS = ['land_size_hectares', 'age'];

const TXT: Record<Lang, Record<string, any>> = {
  en: {
    eyebrow: 'FIND BY NEED', title: 'Tell us what you need', sub: 'Write it in your own words. We will pick out the details, you check them, and only then we look at the schemes.',
    placeholder: 'For example: I have 2 acres in Gujarat and need money to buy a tractor',
    examples: ['I have 2 acres in Gujarat and need money to buy a tractor', 'I am a woman farmer in Punjab and want crop insurance', 'मुझे सिंचाई के लिए सब्सिडी चाहिए'],
    understand: 'Understand my need', understanding: 'Reading your sentence…',
    understood: 'Here is what we understood', understoodSub: 'Please check each detail. Change anything that is wrong and fill in what is missing.',
    lookingFor: 'You are looking for', noTopics: 'No specific topic found. We will use your words as they are.',
    fromSentence: 'from your sentence', aiNote: 'AI reading. Please check this one.', details: 'Your details',
    saveToProfile: 'Also save these details to my farm profile', confirm: 'Looks right. Find schemes', startOver: 'Start over', back: 'Change details',
    resultsFor: 'Schemes for', checking: 'Checking all schemes…', signIn: 'Please sign in to describe your need.', signInBtn: 'Sign in',
    choose: 'Not provided', failed: 'Something went wrong. Please try again.', openProfile: 'Open My Farm',
    fields: { state: 'State', farmer_type: 'Farmer type', land_size_hectares: 'Land size (hectares)', age: 'Age', social_category: 'Social category', gender: 'Gender', primary_crop: 'Main crop' }
  },
  hi: {
    eyebrow: 'ज़रूरत से खोजें', title: 'अपनी ज़रूरत बताएं', sub: 'अपने शब्दों में लिखें। हम जानकारी निकालेंगे, आप उसे जांचेंगे, और उसके बाद ही योजनाएं देखी जाएंगी।',
    placeholder: 'जैसे: मेरे पास गुजरात में 2 एकड़ ज़मीन है और ट्रैक्टर खरीदने के लिए पैसे चाहिए',
    examples: ['मेरे पास गुजरात में 2 एकड़ ज़मीन है और ट्रैक्टर खरीदने के लिए पैसे चाहिए', 'मुझे सिंचाई के लिए सब्सिडी चाहिए', 'I want crop insurance for my wheat'],
    understand: 'मेरी ज़रूरत समझें', understanding: 'आपका वाक्य पढ़ा जा रहा है…',
    understood: 'हमने यह समझा', understoodSub: 'कृपया हर जानकारी जांचें। जो गलत हो बदलें और जो छूटा हो भरें।',
    lookingFor: 'आप ढूंढ रहे हैं', noTopics: 'कोई खास विषय नहीं मिला। हम आपके शब्द जैसे हैं वैसे इस्तेमाल करेंगे।',
    fromSentence: 'आपके वाक्य से', aiNote: 'AI ने पढ़ा है। कृपया इसे जांचें।', details: 'आपकी जानकारी',
    saveToProfile: 'ये जानकारी मेरी फार्म प्रोफाइल में भी सेव करें', confirm: 'सही है। योजनाएं खोजें', startOver: 'फिर से शुरू करें', back: 'जानकारी बदलें',
    resultsFor: 'इसके लिए योजनाएं', checking: 'सभी योजनाएं जांची जा रही हैं…', signIn: 'अपनी ज़रूरत बताने के लिए साइन इन करें।', signInBtn: 'साइन इन',
    choose: 'नहीं दिया', failed: 'कुछ गड़बड़ हुई। कृपया फिर कोशिश करें।', openProfile: 'My Farm खोलें',
    fields: { state: 'राज्य', farmer_type: 'किसान का प्रकार', land_size_hectares: 'ज़मीन (हेक्टेयर)', age: 'उम्र', social_category: 'सामाजिक श्रेणी', gender: 'लिंग', primary_crop: 'मुख्य फसल' }
  },
  hinglish: {
    eyebrow: 'ZAROORAT SE KHOJEIN', title: 'Apni zaroorat batayein', sub: 'Apne shabdon mein likhein. Hum details nikalenge, aap unhe check karenge, aur uske baad hi schemes dekhi jayengi.',
    placeholder: 'Jaise: Mere paas Gujarat mein 2 acre zameen hai aur tractor kharidne ke liye paise chahiye',
    examples: ['Mere paas Gujarat mein 2 acre zameen hai aur tractor kharidne ke liye paise chahiye', 'Mujhe fasal bima chahiye', 'Kheti ke liye loan chahiye, Haryana mein'],
    understand: 'Meri zaroorat samjhein', understanding: 'Aapka vaakya padha ja raha hai…',
    understood: 'Humne ye samjha', understoodSub: 'Har detail check karein. Jo galat ho badlein aur jo chhoot gaya ho bharein.',
    lookingFor: 'Aap dhoondh rahe hain', noTopics: 'Koi khaas topic nahi mila. Hum aapke shabd jaise hain waise use karenge.',
    fromSentence: 'aapke vaakya se', aiNote: 'AI ne padha hai. Ise check karein.', details: 'Aapki details',
    saveToProfile: 'Ye details meri farm profile mein bhi save karein', confirm: 'Sahi hai. Schemes khojein', startOver: 'Phir se shuru karein', back: 'Details badlein',
    resultsFor: 'Iske liye schemes', checking: 'Sabhi schemes check ho rahi hain…', signIn: 'Apni zaroorat batane ke liye sign in karein.', signInBtn: 'Sign in',
    choose: 'Nahi diya', failed: 'Kuch gadbad hui. Phir koshish karein.', openProfile: 'My Farm kholein',
    fields: { state: 'Rajya', farmer_type: 'Kisan ka type', land_size_hectares: 'Zameen (hectare)', age: 'Umr', social_category: 'Social category', gender: 'Gender', primary_crop: 'Main fasal' }
  }
};
export const nt = (lang: Lang, key: string) => TXT[lang]?.[key] ?? TXT.en[key] ?? key;

export function NeedPage({ api, token, lang, profile, seed, nameOf, onOpenScheme, onApplyProfile, onOpenProfile, onLogin }: {
  api: string; token: string; lang: Lang; profile: Record<string, any>; seed: string;
  nameOf: (code: string, fallback: string) => string;
  onOpenScheme: (code: string) => void;
  onApplyProfile: (profile: any, save: boolean) => Promise<void> | void;
  onOpenProfile: () => void; onLogin: () => void;
}) {
  const t = TXT[lang] || TXT.en;
  const [text, setText] = useState(seed || '');
  const [stage, setStage] = useState<'input' | 'confirm' | 'results'>('input');
  const [ex, setEx] = useState<Extraction | null>(null);
  const [draft, setDraft] = useState<Record<string, any>>({});
  const [save, setSave] = useState(false);
  const [results, setResults] = useState<MatchesResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const understand = async (sentence: string) => {
    const s = sentence.trim();
    if (s.length < 3) return;
    setBusy(true); setError('');
    try {
      const r = await fetch(`${api}/api/need/extract`, { method: 'POST', headers, body: JSON.stringify({ text: s, language: lang }) });
      const d = await r.json();
      if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : t.failed);
      setEx(d);
      const next: Record<string, any> = {};
      for (const f of KEY_FIELDS) next[f] = d.fields.find((x: any) => x.field === f)?.value ?? profile[f] ?? '';
      setDraft(next);
      setStage('confirm');
    } catch (e: any) { setError(e.message || t.failed); } finally { setBusy(false); }
  };
  // Arriving from the home-page search box: start reading straight away.
  useEffect(() => { if (seed && token) void understand(seed); }, []);

  const confirmed = (): Record<string, any> => {
    const out: Record<string, any> = { ...profile };
    for (const f of KEY_FIELDS) {
      const v = draft[f];
      if (v === '' || v === undefined || v === null) { delete out[f]; continue; }
      if (NUMBER_FIELDS.includes(f)) { const n = Number(v); if (Number.isNaN(n)) { delete out[f]; continue; } out[f] = n; } else out[f] = v;
    }
    return out;
  };

  const findSchemes = async () => {
    setBusy(true); setError('');
    try {
      const merged = confirmed();
      await onApplyProfile(merged, save);   // the scheme detail view must use the SAME confirmed details
      const r = await fetch(`${api}/api/matches/preview`, { method: 'POST', headers, body: JSON.stringify({ profile: merged, need_text: text }) });
      const d = await r.json();
      if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : t.failed);
      setResults(d); setStage('results');
    } catch (e: any) { setError(e.message || t.failed); } finally { setBusy(false); }
  };

  const reset = () => { setStage('input'); setEx(null); setResults(null); setError(''); };
  const head = (
    <div className="pageIntro"><div>
      <p className="eyebrow dark">{t.eyebrow}</p><h2>{t.title}</h2><p>{t.sub}</p>
    </div></div>
  );

  if (!token) return <section className="section page">{head}<p>{t.signIn}</p><button className="primary" onClick={onLogin}>{t.signInBtn}</button></section>;

  if (stage === 'input') return (
    <section className="section page">{head}
      <textarea className="needText" rows={4} maxLength={1000} value={text} placeholder={t.placeholder} onChange={e => setText(e.target.value)} />
      <div className="needExamples">{(t.examples as string[]).map(x => <button key={x} type="button" className="needChip" onClick={() => setText(x)}>{x}</button>)}</div>
      {error && <p className="matchError">{error}</p>}
      <button className="primary" disabled={busy || text.trim().length < 3} onClick={() => understand(text)}>{busy ? t.understanding : t.understand}</button>
    </section>
  );

  if (stage === 'confirm' && ex) return (
    <section className="section page">{head}
      <div className="needQuote">“{ex.text}”</div>
      <h3>{t.understood}</h3>
      <p className="matchGroupDesc">{t.understoodSub}</p>
      <p className="needTopics"><b>{t.lookingFor}:</b> {ex.topics.length ? ex.topics.map(x => <span key={x.id} className="matchChip eligible">{x.label}</span>) : <span>{t.noTopics}</span>}</p>
      {ex.notes.length > 0 && <ul className="needNotes">{ex.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>}
      <h4>{t.details}</h4>
      <div className="needGrid">
        {KEY_FIELDS.map(f => {
          const found = ex.fields.find(x => x.field === f);
          const options = PROFILE_OPTIONS[f] || [];
          const value = draft[f] ?? '';
          return (
            <label key={f} className={found ? 'needField found' : 'needField'}>
              <span>{t.fields[f]}</span>
              {SELECT_FIELDS.includes(f) ? (
                <select value={value} onChange={e => setDraft({ ...draft, [f]: e.target.value })}>
                  <option value="">{t.choose}</option>
                  {value && !options.some(o => o.value === value) && <option value={value}>{String(value)}</option>}
                  {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              ) : (
                <input type={NUMBER_FIELDS.includes(f) ? 'number' : 'text'} min={NUMBER_FIELDS.includes(f) ? 0 : undefined} step={f === 'land_size_hectares' ? 0.01 : undefined}
                  value={value} onChange={e => setDraft({ ...draft, [f]: e.target.value })} />
              )}
              {found && <small className="needEvidence">{found.source === 'ai' ? t.aiNote : `${t.fromSentence}: “${found.evidence}”`}</small>}
            </label>
          );
        })}
      </div>
      <label className="needSave"><input type="checkbox" checked={save} onChange={e => setSave(e.target.checked)} /> {t.saveToProfile}</label>
      {error && <p className="matchError">{error}</p>}
      <div className="pageActions">
        <button className="primary" disabled={busy} onClick={findSchemes}>{busy ? t.checking : t.confirm}</button>
        <button className="outline" disabled={busy} onClick={reset}>{t.startOver}</button>
      </div>
    </section>
  );

  return (
    <section className="section page">{head}
      <div className="needQuote">{t.resultsFor}: “{text}”</div>
      <div className="pageActions">
        <button className="outline" onClick={() => setStage('confirm')}>{t.back}</button>
        <button className="outline" onClick={reset}>{t.startOver}</button>
      </div>
      {results && <MatchResults data={results} lang={lang} nameOf={nameOf} onOpen={onOpenScheme} />}
    </section>
  );
}
