// Documents: upload once, reuse for every scheme.
//   DocumentsPage      the full vault (upload, view, download, change type, delete)
//   ProfileDocuments   "upload the documents most schemes ask for", shown under the farm profile
//   DocumentPlan       inside "Plan application": what this scheme asks for, what is already uploaded,
//                      and next steps for anything the farmer does not have
//   DocumentSummary    one line on the scheme details ("3 of 5 documents ready")
import React, { useCallback, useEffect, useState } from 'react';

type Lang = 'en' | 'hi' | 'hinglish';
type DocType = { id: string; label: Record<Lang, string>; usedBySchemes: number };
type Doc = { id: number; docType: string; name: string; contentType: string; sizeBytes: number; note: string | null; uploadedAt: string };
type Limits = { maxFileBytes: number; maxDocuments: number; maxTotalBytes: number };
type HowTo = { title: Record<Lang, string>; steps: Record<Lang, string[]>; links: { label: string; url: string }[] };
type PlanItem = { name: string; purpose?: string | null; requiredType: string; suggestedType: string; matchable: boolean; status: string; choice: string | null; documentIds: number[]; howToGet: HowTo | null };
type Plan = { schemeCode: string; items: PlanItem[]; nextSteps: { name: string; suggestedType: string; requiredType: string; howToGet: HowTo }[]; summary: Record<string, number> };

const TXT: Record<Lang, Record<string, string>> = {
  en: {
    navLabel: 'Documents', eyebrow: 'MY DOCUMENTS', title: 'My documents', sub: 'Upload the documents most schemes ask for, once. We reuse them for every scheme and tell you what else is needed.',
    privacy: 'Only you can see your documents. They are kept on the KrishiAssist server and are not shared. PDF, JPEG or PNG only, up to {mb} MB each.',
    signIn: 'Please sign in to manage your documents.', signInBtn: 'Sign in', loading: 'Loading…',
    starterTitle: 'Upload your key documents now', starterSub: 'These are asked for by the most schemes. Uploading them once saves time later.', askedBy: 'Asked by {n} schemes',
    uploaded: 'Uploaded', upload: 'Upload', uploading: 'Uploading…', manageAll: 'Manage all my documents →',
    kind: 'Document type', file: 'File', note: 'Note (optional)', uploadBtn: 'Upload document', yourDocs: 'Your documents', empty: 'You have not uploaded any document yet.',
    view: 'View', download: 'Download', del: 'Delete', confirmDelete: 'Delete this document? This cannot be undone.', changeType: 'Document type',
    usage: '{count} of {max} documents · {used} of {total} used', tooBig: 'This file is larger than {mb} MB.', badType: 'Only PDF, JPEG or PNG files can be uploaded.',
    failed: 'Upload failed.', okUp: 'Document uploaded.', okDel: 'Document deleted.', chooseFile: 'Choose a file first.',
    planTitle: 'Documents for this scheme', planSub: 'Documents you have already uploaded are matched automatically. Tell us about the rest.',
    ready: 'Ready', readySelf: 'You have it', notApplicable: 'Not applicable', toArrange: 'To arrange', undecided: 'Needs your answer',
    required: 'Required', conditional: 'If applicable', verification: 'Shown at verification',
    uploadNow: 'Upload now', haveIt: 'I have it', dontHave: "I don't have it yet", notApp: 'Not applicable to me', changeAnswer: 'Change answer',
    planSummary: '{ready} of {total} ready · {arrange} to arrange · {undecided} need your answer', open: '{n} required documents still open',
    nextTitle: 'Next steps: documents to arrange', nextEmpty: 'Nothing to arrange right now. If a document is missing, choose "I don\'t have it yet" and the steps appear here.',
    howTo: 'How to get this', stateNote: 'Offices and portals differ by state. Please confirm with the official office or portal before you go.', openLink: 'Open',
    sumLine: 'Documents: {ready} of {total} ready', prepare: 'Prepare documents', clear: 'Clear',
  },
  hi: {
    navLabel: 'दस्तावेज़', eyebrow: 'मेरे दस्तावेज़', title: 'मेरे दस्तावेज़', sub: 'जो दस्तावेज़ ज़्यादातर योजनाएं मांगती हैं, उन्हें एक बार अपलोड करें। हम उन्हें हर योजना में इस्तेमाल करेंगे और बताएंगे कि और क्या चाहिए।',
    privacy: 'आपके दस्तावेज़ सिर्फ़ आप देख सकते हैं। वे KrishiAssist सर्वर पर रखे जाते हैं और किसी से साझा नहीं होते। सिर्फ़ PDF, JPEG या PNG, हर फ़ाइल {mb} MB तक।',
    signIn: 'अपने दस्तावेज़ संभालने के लिए साइन इन करें।', signInBtn: 'साइन इन', loading: 'लोड हो रहा है…',
    starterTitle: 'अभी अपने मुख्य दस्तावेज़ अपलोड करें', starterSub: 'इन्हें सबसे ज़्यादा योजनाएं मांगती हैं। एक बार अपलोड करने से आगे समय बचता है।', askedBy: '{n} योजनाओं में ज़रूरी',
    uploaded: 'अपलोड हो गया', upload: 'अपलोड करें', uploading: 'अपलोड हो रहा है…', manageAll: 'मेरे सभी दस्तावेज़ देखें →',
    kind: 'दस्तावेज़ का प्रकार', file: 'फ़ाइल', note: 'नोट (वैकल्पिक)', uploadBtn: 'दस्तावेज़ अपलोड करें', yourDocs: 'आपके दस्तावेज़', empty: 'आपने अभी कोई दस्तावेज़ अपलोड नहीं किया है।',
    view: 'देखें', download: 'डाउनलोड', del: 'हटाएं', confirmDelete: 'यह दस्तावेज़ हटाएं? इसे वापस नहीं लाया जा सकता।', changeType: 'दस्तावेज़ का प्रकार',
    usage: '{max} में से {count} दस्तावेज़ · {total} में से {used} उपयोग में', tooBig: 'यह फ़ाइल {mb} MB से बड़ी है।', badType: 'सिर्फ़ PDF, JPEG या PNG फ़ाइलें अपलोड हो सकती हैं।',
    failed: 'अपलोड नहीं हो सका।', okUp: 'दस्तावेज़ अपलोड हो गया।', okDel: 'दस्तावेज़ हटा दिया गया।', chooseFile: 'पहले फ़ाइल चुनें।',
    planTitle: 'इस योजना के दस्तावेज़', planSub: 'जो दस्तावेज़ आप पहले अपलोड कर चुके हैं वे अपने-आप जुड़ जाते हैं। बाकी के बारे में बताइए।',
    ready: 'तैयार', readySelf: 'आपके पास है', notApplicable: 'लागू नहीं', toArrange: 'जुटाना है', undecided: 'आपका जवाब चाहिए',
    required: 'ज़रूरी', conditional: 'यदि लागू हो', verification: 'सत्यापन के समय दिखाना है',
    uploadNow: 'अभी अपलोड करें', haveIt: 'मेरे पास है', dontHave: 'मेरे पास अभी नहीं है', notApp: 'मुझ पर लागू नहीं', changeAnswer: 'जवाब बदलें',
    planSummary: '{total} में से {ready} तैयार · {arrange} जुटाने हैं · {undecided} का जवाब चाहिए', open: '{n} ज़रूरी दस्तावेज़ अभी बाकी हैं',
    nextTitle: 'अगले कदम: जो दस्तावेज़ जुटाने हैं', nextEmpty: 'अभी कुछ जुटाना नहीं है। कोई दस्तावेज़ न हो तो "मेरे पास अभी नहीं है" चुनें, कदम यहां दिखेंगे।',
    howTo: 'यह कैसे मिलेगा', stateNote: 'दफ़्तर और पोर्टल राज्य के हिसाब से अलग होते हैं। जाने से पहले आधिकारिक दफ़्तर या पोर्टल से पुष्टि कर लें।', openLink: 'खोलें',
    sumLine: 'दस्तावेज़: {total} में से {ready} तैयार', prepare: 'दस्तावेज़ तैयार करें', clear: 'हटाएं',
  },
  hinglish: {
    navLabel: 'Documents', eyebrow: 'MERE DOCUMENTS', title: 'Mere documents', sub: 'Jo documents zyadatar schemes maangti hain, unhe ek baar upload karein. Hum unhe har scheme mein use karenge aur batayenge ki aur kya chahiye.',
    privacy: 'Aapke documents sirf aap dekh sakte hain. Ye KrishiAssist server par rakhe jaate hain aur kisi se share nahi hote. Sirf PDF, JPEG ya PNG, har file {mb} MB tak.',
    signIn: 'Apne documents sambhalne ke liye sign in karein.', signInBtn: 'Sign in', loading: 'Load ho raha hai…',
    starterTitle: 'Abhi apne mukhya documents upload karein', starterSub: 'Inhe sabse zyada schemes maangti hain. Ek baar upload karne se aage time bachta hai.', askedBy: '{n} schemes mein zaroori',
    uploaded: 'Upload ho gaya', upload: 'Upload karein', uploading: 'Upload ho raha hai…', manageAll: 'Mere sabhi documents dekhein →',
    kind: 'Document ka type', file: 'File', note: 'Note (optional)', uploadBtn: 'Document upload karein', yourDocs: 'Aapke documents', empty: 'Aapne abhi koi document upload nahi kiya hai.',
    view: 'Dekhein', download: 'Download', del: 'Hatayein', confirmDelete: 'Ye document hatayein? Ise wapas nahi laaya ja sakta.', changeType: 'Document ka type',
    usage: '{max} mein se {count} documents · {total} mein se {used} use mein', tooBig: 'Ye file {mb} MB se badi hai.', badType: 'Sirf PDF, JPEG ya PNG files upload ho sakti hain.',
    failed: 'Upload nahi ho saka.', okUp: 'Document upload ho gaya.', okDel: 'Document hata diya gaya.', chooseFile: 'Pehle file chunein.',
    planTitle: 'Is scheme ke documents', planSub: 'Jo documents aap pehle upload kar chuke hain wo apne-aap jud jaate hain. Baaki ke bare mein batayein.',
    ready: 'Taiyaar', readySelf: 'Aapke paas hai', notApplicable: 'Lagu nahi', toArrange: 'Jutana hai', undecided: 'Aapka jawab chahiye',
    required: 'Zaroori', conditional: 'Agar lagu ho', verification: 'Verification ke samay dikhana hai',
    uploadNow: 'Abhi upload karein', haveIt: 'Mere paas hai', dontHave: 'Mere paas abhi nahi hai', notApp: 'Mujh par lagu nahi', changeAnswer: 'Jawab badlein',
    planSummary: '{total} mein se {ready} taiyaar · {arrange} jutane hain · {undecided} ka jawab chahiye', open: '{n} zaroori documents abhi baaki hain',
    nextTitle: 'Agle kadam: jo documents jutane hain', nextEmpty: 'Abhi kuch jutana nahi hai. Koi document na ho to "Mere paas abhi nahi hai" chunein, steps yahan dikhenge.',
    howTo: 'Ye kaise milega', stateNote: 'Offices aur portals rajya ke hisaab se alag hote hain. Jaane se pehle official office ya portal se confirm kar lein.', openLink: 'Kholein',
    sumLine: 'Documents: {total} mein se {ready} taiyaar', prepare: 'Documents taiyaar karein', clear: 'Hatayein',
  },
};
const fmt = (lang: Lang, key: string, v?: Record<string, string | number>) => {
  const s = TXT[lang]?.[key] ?? TXT.en[key] ?? key;
  return v ? s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? '')) : s;
};
const size = (n: number) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);
const asUtc = (s: string) => (/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z');
const day = (s: string, lang: Lang) => { try { return new Date(asUtc(s)).toLocaleDateString(lang === 'en' ? 'en-IN' : 'hi-IN', { dateStyle: 'medium' }); } catch { return s; } };
const ACCEPT = '.pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png';
const looksAllowed = (f: File) => /\.(pdf|jpe?g|png)$/i.test(f.name) || ['application/pdf', 'image/jpeg', 'image/png'].includes(f.type);

type Common = { api: string; token: string; lang: Lang; notify: (m: string) => void };

/** Everything the vault pages share: the document types, the farmer's files, and the actions on them. */
function useVault({ api, token, lang, notify }: Common) {
  const [types, setTypes] = useState<DocType[]>([]);
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [usage, setUsage] = useState({ count: 0, bytes: 0 });
  const [limits, setLimits] = useState<Limits>({ maxFileBytes: 5242880, maxDocuments: 25, maxTotalBytes: 52428800 });
  const [busy, setBusy] = useState('');
  const auth = { Authorization: `Bearer ${token}` };

  const reload = useCallback(async () => {
    if (!token) return;
    try {
      const [t, d] = await Promise.all([fetch(`${api}/api/documents/types`), fetch(`${api}/api/documents`, { headers: auth })]);
      if (t.ok) setTypes(await t.json());
      if (d.ok) { const j = await d.json(); setDocs(j.documents); setUsage(j.usage); setLimits(j.limits); }
    } catch { notify(fmt(lang, 'failed')); }
  }, [api, token]);
  useEffect(() => { void reload(); }, [reload]);

  /** Send one file. The file is the request body; the details travel in the address. Returns true when saved. */
  const send = async (file: File, docType: string, note = ''): Promise<boolean> => {
    if (!looksAllowed(file)) { notify(fmt(lang, 'badType')); return false; }
    if (file.size > limits.maxFileBytes) { notify(fmt(lang, 'tooBig', { mb: Math.round(limits.maxFileBytes / 1048576) })); return false; }
    setBusy('upload');
    try {
      const q = new URLSearchParams({ doc_type: docType, filename: file.name });
      if (note.trim()) q.set('note', note.trim());
      const r = await fetch(`${api}/api/documents?${q}`, { method: 'POST', headers: { ...auth, 'Content-Type': 'application/octet-stream' }, body: await file.arrayBuffer() });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { notify(typeof d.detail === 'string' ? d.detail : fmt(lang, 'failed')); return false; }
      notify(fmt(lang, 'okUp'));
      await reload();
      return true;
    } catch { notify(fmt(lang, 'failed')); return false; } finally { setBusy(''); }
  };

  /** View in a new tab, or download. Files need the sign-in token, so they are fetched and shown from memory. */
  const openFile = async (doc: { id: number; name: string }, download = false) => {
    const tab = download ? null : window.open('', '_blank');
    try {
      const r = await fetch(`${api}/api/documents/${doc.id}/file${download ? '?download=1' : ''}`, { headers: auth });
      if (!r.ok) { tab?.close(); const d = await r.json().catch(() => ({})); notify(typeof d.detail === 'string' ? d.detail : fmt(lang, 'failed')); return; }
      const url = URL.createObjectURL(await r.blob());
      if (download) { const a = document.createElement('a'); a.href = url; a.download = doc.name; document.body.appendChild(a); a.click(); a.remove(); }
      else if (tab) tab.location.href = url;
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch { tab?.close(); notify(fmt(lang, 'failed')); }
  };

  const remove = async (doc: Doc) => {
    if (!window.confirm(fmt(lang, 'confirmDelete'))) return;
    const r = await fetch(`${api}/api/documents/${doc.id}`, { method: 'DELETE', headers: auth });
    if (r.ok) { notify(fmt(lang, 'okDel')); await reload(); }
  };
  const retype = async (doc: Doc, docType: string) => {
    const r = await fetch(`${api}/api/documents/${doc.id}`, { method: 'PATCH', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify({ doc_type: docType }) });
    if (r.ok) await reload();
  };
  return { types, docs, usage, limits, busy, send, openFile, remove, retype, reload };
}

/** A button that opens the file picker. The real input stays in the page so keyboards and screen readers can use it. */
function PickFile({ label, onFile, disabled, className = 'outline' }: { label: string; onFile: (f: File) => void; disabled?: boolean; className?: string }) {
  return (
    <label className={`dv-pick ${className}${disabled ? ' disabled' : ''}`}>
      {label}
      <input type="file" accept={ACCEPT} disabled={disabled} onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f); e.target.value = ''; }} />
    </label>
  );
}

/* ---------------- starter documents (profile page and top of the vault) ---------------- */
function StarterDocuments(p: Common & { vault: ReturnType<typeof useVault>; onManage?: () => void }) {
  const { lang, vault: v } = p;
  const starters = [...v.types].filter(t => t.id !== 'other' && t.usedBySchemes > 0).sort((a, b) => b.usedBySchemes - a.usedBySchemes).slice(0, 5);
  if (!starters.length) return null;
  return (
    <div className="dv-card dv-starter">
      <h3>{fmt(lang, 'starterTitle')}</h3>
      <p>{fmt(lang, 'starterSub')}</p>
      <ul className="dv-list">
        {starters.map(t => {
          const have = (v.docs || []).filter(d => d.docType === t.id);
          return (
            <li key={t.id} className="dv-row">
              <div className="dv-main"><b>{t.label[lang]}</b><small>{fmt(lang, 'askedBy', { n: t.usedBySchemes })}</small></div>
              <div className="dv-actions">
                {have.length > 0 && <span className="dv-chip ok">✓ {fmt(lang, 'uploaded')}</span>}
                {have.length > 0 && <button type="button" className="outline" onClick={() => v.openFile(have[0])}>{fmt(lang, 'view')}</button>}
                {have.length === 0 && <PickFile label={v.busy === 'upload' ? fmt(lang, 'uploading') : fmt(lang, 'upload')} disabled={v.busy === 'upload'} onFile={f => v.send(f, t.id)} className="primary" />}
              </div>
            </li>
          );
        })}
      </ul>
      {p.onManage && <button type="button" className="dv-link" onClick={p.onManage}>{fmt(lang, 'manageAll')}</button>}
    </div>
  );
}

/* ---------------- the full page ---------------- */
export function DocumentsPage(p: Common & { onLogin: () => void }) {
  const { lang } = p;
  const v = useVault(p);
  const [docType, setDocType] = useState('land_record');
  const [note, setNote] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const head = (
    <div className="pageIntro"><div><p className="eyebrow dark">{fmt(lang, 'eyebrow')}</p><h2>{fmt(lang, 'title')}</h2><p>{fmt(lang, 'sub')}</p></div></div>
  );
  if (!p.token) return <section className="section page">{head}<p>{fmt(lang, 'signIn')}</p><button className="primary" onClick={p.onLogin}>{fmt(lang, 'signInBtn')}</button></section>;

  const submit = async () => {
    if (!file) { p.notify(fmt(lang, 'chooseFile')); return; }
    if (await v.send(file, docType, note)) { setFile(null); setNote(''); }
  };
  const mb = Math.round(v.limits.maxFileBytes / 1048576);

  return (
    <section className="section page documentsPage">
      {head}
      <p className="dv-privacy">🔒 {fmt(lang, 'privacy', { mb })}</p>
      <StarterDocuments {...p} vault={v} />

      <div className="dv-card">
        <h3>{fmt(lang, 'uploadBtn')}</h3>
        <div className="dv-form">
          <label>{fmt(lang, 'kind')}
            <select value={docType} onChange={e => setDocType(e.target.value)}>{v.types.map(t => <option key={t.id} value={t.id}>{t.label[lang]}</option>)}</select>
          </label>
          <label>{fmt(lang, 'note')}
            <input value={note} maxLength={300} onChange={e => setNote(e.target.value)} />
          </label>
          <div className="dv-formfile">
            <PickFile label={file ? file.name : fmt(lang, 'file')} onFile={setFile} />
            <button type="button" className="primary" disabled={v.busy === 'upload'} onClick={submit}>{v.busy === 'upload' ? fmt(lang, 'uploading') : fmt(lang, 'uploadBtn')}</button>
          </div>
        </div>
      </div>

      <div className="dv-card dv-vault">
        <h3>{fmt(lang, 'yourDocs')}</h3>
        <p className="dv-usage">{fmt(lang, 'usage', { count: v.usage.count, max: v.limits.maxDocuments, used: size(v.usage.bytes), total: size(v.limits.maxTotalBytes) })}</p>
        {v.docs === null ? <p>{fmt(lang, 'loading')}</p> : v.docs.length === 0 ? <p>{fmt(lang, 'empty')}</p> : (
          <ul className="dv-list">
            {v.docs.map(d => (
              <li key={d.id} className="dv-row">
                <div className="dv-main">
                  <b>{d.name}</b>
                  <small>{size(d.sizeBytes)} · {day(d.uploadedAt, lang)}{d.note ? ` · ${d.note}` : ''}</small>
                  <label className="dv-type">{fmt(lang, 'changeType')}
                    <select value={d.docType} onChange={e => v.retype(d, e.target.value)}>{v.types.map(t => <option key={t.id} value={t.id}>{t.label[lang]}</option>)}</select>
                  </label>
                </div>
                <div className="dv-actions">
                  <button type="button" className="outline" onClick={() => v.openFile(d)}>{fmt(lang, 'view')}</button>
                  <button type="button" className="outline" onClick={() => v.openFile(d, true)}>{fmt(lang, 'download')}</button>
                  <button type="button" className="dv-danger" onClick={() => v.remove(d)}>{fmt(lang, 'del')}</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

/** Shown under the farm profile: upload the documents most schemes ask for. */
export function ProfileDocuments(p: Common & { onManage: () => void }) {
  const v = useVault(p);
  return (
    <section className="section page dv-profile">
      <p className="dv-privacy">🔒 {fmt(p.lang, 'privacy', { mb: Math.round(v.limits.maxFileBytes / 1048576) })}</p>
      <StarterDocuments {...p} vault={v} />
    </section>
  );
}

/* ---------------- the plan for one scheme ---------------- */
export function DocumentPlan(p: Common & { schemeCode: string; onManage: () => void }) {
  const { lang } = p;
  const v = useVault(p);
  const [plan, setPlan] = useState<Plan | null>(null);
  const auth = { Authorization: `Bearer ${p.token}` };

  const load = useCallback(async () => {
    const r = await fetch(`${p.api}/api/documents/plan/${encodeURIComponent(p.schemeCode)}`, { headers: auth });
    if (r.ok) setPlan(await r.json());
  }, [p.api, p.token, p.schemeCode]);
  useEffect(() => { void load(); }, [load]);

  const choose = async (name: string, choice: string | null) => {
    const r = await fetch(`${p.api}/api/documents/plan/${encodeURIComponent(p.schemeCode)}`, { method: 'PUT', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify({ document_name: name, choice }) });
    if (r.ok) setPlan(await r.json()); else p.notify(fmt(lang, 'failed'));
  };
  const uploadFor = async (item: PlanItem, file: File) => { if (await v.send(file, item.suggestedType)) await load(); };

  if (!plan) return <div className="plannerSection"><h3>1. {fmt(lang, 'planTitle')}</h3><p>{fmt(lang, 'loading')}</p></div>;
  const s = plan.summary;
  const groups: [string, PlanItem[]][] = (['required', 'conditional', 'verification'] as const).map(g => [g, plan.items.filter(i => i.requiredType === g)] as [string, PlanItem[]]).filter(([, items]) => items.length);
  const chip = (i: PlanItem) => {
    const map: Record<string, [string, string]> = { ready: ['ok', 'ready'], ready_self: ['ok', 'readySelf'], not_applicable: ['mute', 'notApplicable'], to_arrange: ['warn', 'toArrange'], undecided: ['ask', 'undecided'] };
    const [tone, key] = map[i.status] || ['mute', 'undecided'];
    return <span className={`dv-chip ${tone}`}>{i.status === 'ready' ? '✓ ' : ''}{fmt(lang, key)}</span>;
  };

  return (
    <div className="plannerSection documentPlan">
      <h3>1. {fmt(lang, 'planTitle')}</h3>
      <p>{fmt(lang, 'planSub')}</p>
      <p className="dv-summary"><b>{fmt(lang, 'planSummary', { ready: s.ready, total: s.total, arrange: s.toArrange, undecided: s.undecided })}</b>{s.requiredOpen > 0 && <span> · {fmt(lang, 'open', { n: s.requiredOpen })}</span>}</p>

      {groups.map(([g, items]) => (
        <div key={g} className="dv-group">
          <h4>{fmt(lang, g)}</h4>
          <ul className="dv-list">
            {items.map(i => (
              <li key={i.name} className={`dv-row dv-item ${i.status}`}>
                <div className="dv-main">
                  <b>{i.name}</b>{i.purpose && <small>{i.purpose}</small>}
                  <div className="dv-chips">{chip(i)}</div>
                  {i.status === 'undecided' && i.howToGet && (
                    <details className="dv-how"><summary>{fmt(lang, 'howTo')}</summary>
                      <ol>{i.howToGet.steps[lang].map((st, n) => <li key={n}>{st}</li>)}</ol>
                    </details>
                  )}
                </div>
                <div className="dv-actions">
                  {i.status === 'ready' && i.documentIds[0] && <button type="button" className="outline" onClick={() => v.openFile({ id: i.documentIds[0], name: i.name })}>{fmt(lang, 'view')}</button>}
                  {(i.status === 'undecided' || i.status === 'to_arrange') && (<>
                    {i.matchable && <PickFile label={fmt(lang, 'uploadNow')} disabled={v.busy === 'upload'} onFile={f => uploadFor(i, f)} className="primary" />}
                    {i.status === 'undecided' && <button type="button" className="outline" onClick={() => choose(i.name, 'have_it')}>{fmt(lang, 'haveIt')}</button>}
                    {i.status === 'undecided' && <button type="button" className="outline" onClick={() => choose(i.name, 'dont_have')}>{fmt(lang, 'dontHave')}</button>}
                    {i.status === 'undecided' && <button type="button" className="outline" onClick={() => choose(i.name, 'not_applicable')}>{fmt(lang, 'notApp')}</button>}
                    {i.status === 'to_arrange' && <button type="button" className="dv-link" onClick={() => choose(i.name, null)}>{fmt(lang, 'changeAnswer')}</button>}
                  </>)}
                  {(i.status === 'ready_self' || i.status === 'not_applicable') && <button type="button" className="dv-link" onClick={() => choose(i.name, null)}>{fmt(lang, 'changeAnswer')}</button>}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}

      <div className="dv-next">
        <h4>{fmt(lang, 'nextTitle')}</h4>
        {plan.nextSteps.length === 0 ? <p>{fmt(lang, 'nextEmpty')}</p> : (
          <>
            {plan.nextSteps.map((n, idx) => (
              <article key={n.name} className="dv-step">
                <h5><span className="dv-num">{idx + 1}</span>{n.name}<small>{n.howToGet.title[lang]}</small></h5>
                <ol>{n.howToGet.steps[lang].map((st, k) => <li key={k}>{st}</li>)}</ol>
                {n.howToGet.links.length > 0 && <p className="dv-links">{n.howToGet.links.map(l => <a key={l.url} href={l.url} target="_blank" rel="noreferrer">{l.label} ↗</a>)}</p>}
              </article>
            ))}
            <p className="dv-statenote">{fmt(lang, 'stateNote')}</p>
          </>
        )}
      </div>
      <button type="button" className="dv-link" onClick={p.onManage}>{fmt(lang, 'manageAll')}</button>
    </div>
  );
}

/* ---------------- one line on the scheme details and on each application ---------------- */
export function DocumentSummary(p: Common & { schemeCode: string; onPrepare: () => void }) {
  const [plan, setPlan] = useState<Plan | null>(null);
  useEffect(() => {
    fetch(`${p.api}/api/documents/plan/${encodeURIComponent(p.schemeCode)}`, { headers: { Authorization: `Bearer ${p.token}` } })
      .then(r => (r.ok ? r.json() : null)).then(setPlan).catch(() => setPlan(null));
  }, [p.api, p.token, p.schemeCode]);
  if (!plan || !plan.summary.total) return null;
  const s = plan.summary;
  return (
    <div className="dv-summaryline">
      <span>📄 {fmt(p.lang, 'sumLine', { ready: s.ready, total: s.total })}</span>
      <div className="dv-bar"><span style={{ width: `${Math.round((100 * s.ready) / s.total)}%` }} /></div>
      <button type="button" className="outline" onClick={p.onPrepare}>{fmt(p.lang, 'prepare')}</button>
    </div>
  );
}
