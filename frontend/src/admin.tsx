// Administrator page: coverage report, scheme switches and verification dates, and a checker
// for new scheme files. The server enforces every rule here; this page only shows the controls.
// It is written in English on purpose: it is a staff tool, not a farmer screen.
import React, { useEffect, useState } from 'react';

type Row = {
  schemeCode: string; name: string; state: string | null; category: string | null; status: string; fileStatus: string;
  lastVerifiedAt: string | null; overridden: boolean; criteriaCount: number; sourceCount: number; sourcesWithUrl: number;
};
type Edit = { status: string; date: string; ack: boolean };
const STATUSES = ['active', 'verification_required', 'inactive'];
const STATUS_LABEL: Record<string, string> = { active: 'Active (verified)', verification_required: 'Needs verification', inactive: 'Switched off' };
const today = () => new Date().toISOString().slice(0, 10);

export function AdminPage({ api, token, onLogin }: { api: string; token: string; onLogin: () => void }) {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [report, setReport] = useState<any | null>(null);
  const [denied, setDenied] = useState(false);
  const [error, setError] = useState('');
  const [edits, setEdits] = useState<Record<string, Edit>>({});
  const [messages, setMessages] = useState<Record<string, string>>({});
  const [needsAck, setNeedsAck] = useState<Record<string, boolean>>({});
  const [json, setJson] = useState('');
  const [validation, setValidation] = useState<{ valid: boolean; errors: string[]; warnings: string[] } | null>(null);
  const [filter, setFilter] = useState('');
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const load = async () => {
    setError('');
    try {
      const [a, b] = await Promise.all([fetch(`${api}/api/admin/schemes`, { headers }), fetch(`${api}/api/admin/coverage`, { headers })]);
      if (a.status === 403 || b.status === 403) { setDenied(true); return; }
      if (!a.ok || !b.ok) throw new Error('Could not load the admin data.');
      setRows(await a.json()); setReport(await b.json()); setEdits({});
    } catch (e: any) { setError(e.message); }
  };
  useEffect(() => { if (token) void load(); }, [token]);

  const current = (r: Row): Edit => edits[r.schemeCode] || { status: r.status, date: r.lastVerifiedAt || '', ack: false };
  const change = (r: Row, patch: Partial<Edit>) => setEdits({ ...edits, [r.schemeCode]: { ...current(r), ...patch } });

  const save = async (r: Row, override?: Partial<Edit>) => {
    const e = { ...current(r), ...override };
    setMessages({ ...messages, [r.schemeCode]: '' });
    const res = await fetch(`${api}/api/admin/schemes/${encodeURIComponent(r.schemeCode)}`, {
      method: 'PUT', headers,
      body: JSON.stringify({ status: e.status, last_verified_at: e.date || null, acknowledge_single_rule: e.ack }),
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) {
      setMessages({ ...messages, [r.schemeCode]: typeof d.detail === 'string' ? d.detail : 'Could not save.' });
      if (res.status === 409) setNeedsAck({ ...needsAck, [r.schemeCode]: true });
      return;
    }
    setNeedsAck({ ...needsAck, [r.schemeCode]: false });
    await load();
  };

  const revert = async (r: Row) => {
    const res = await fetch(`${api}/api/admin/schemes/${encodeURIComponent(r.schemeCode)}/override`, { method: 'DELETE', headers });
    if (res.ok) await load();
  };

  const validate = async () => {
    let scheme: unknown;
    try { scheme = JSON.parse(json); } catch { setValidation({ valid: false, errors: ['That is not valid JSON. Check commas and quotes.'], warnings: [] }); return; }
    const res = await fetch(`${api}/api/admin/schemes/validate`, { method: 'POST', headers, body: JSON.stringify({ scheme }) });
    const d = await res.json();
    setValidation(res.ok ? d : { valid: false, errors: [typeof d.detail === 'string' ? d.detail : 'The scheme must be a JSON object.'], warnings: [] });
  };

  const head = <div className="pageIntro"><div><p className="eyebrow dark">ADMINISTRATOR</p><h2>Scheme administration</h2><p>Switch schemes on or off, record when they were checked against the official source, and see where the data is thin. Changes apply to farmers immediately and never rewrite schemes.json.</p></div></div>;
  if (!token) return <section className="section page">{head}<button className="primary" onClick={onLogin}>Sign in</button></section>;
  if (denied) return <section className="section page">{head}<p className="matchError">Administrator access is required for this page.</p></section>;
  if (error) return <section className="section page">{head}<p className="matchError">{error}</p></section>;
  if (!rows || !report) return <section className="section page">{head}<p>Loading…</p></section>;

  const visible = rows.filter(r => !filter || `${r.schemeCode} ${r.name} ${r.state}`.toLowerCase().includes(filter.toLowerCase()));
  const gaps = report.gaps as Record<string, string[]>;
  const GAP_LABEL: Record<string, string> = {
    neverVerified: 'Never verified', staleVerification: `Verified more than ${report.staleAfterDays} days ago`, noSourceUrl: 'No source link',
    hindiMissing: 'Hindi text missing', singleRuleOnly: 'Only one eligibility rule',
  };

  return (
    <section className="section page">{head}
      <div className="adminCards">
        {Object.entries(report.totals).map(([k, v]) => <div key={k} className="adminCard"><b>{String(v)}</b><span>{k === 'schemes' ? 'Schemes in total' : STATUS_LABEL[k] || k}</span></div>)}
        {Object.entries(report.usage).map(([k, v]) => <div key={k} className="adminCard muted"><b>{String(v)}</b><span>{k}</span></div>)}
      </div>

      <h3>Where the data is thin</h3>
      <div className="adminGaps">
        {Object.entries(gaps).map(([k, codes]) => (
          <details key={k}><summary>{GAP_LABEL[k] || k} <b>({codes.length})</b></summary><p>{codes.length ? codes.join(', ') : 'None'}</p></details>
        ))}
        <details><summary>States with no scheme in the system <b>({report.statesWithoutSchemes.length})</b></summary><p>{report.statesWithoutSchemes.join(', ')}</p></details>
      </div>

      <h3>Schemes</h3>
      <input className="adminFilter" placeholder="Filter by code, name or state" value={filter} onChange={e => setFilter(e.target.value)} />
      <div className="adminTableWrap">
        <table className="adminTable">
          <thead><tr><th>Scheme</th><th>Status</th><th>Last verified</th><th>Rules</th><th>Actions</th></tr></thead>
          <tbody>
            {visible.map(r => {
              const e = current(r);
              return (
                <tr key={r.schemeCode} className={r.overridden ? 'overridden' : ''}>
                  <td><b>{r.schemeCode}</b><small>{r.name}</small><small>{r.state}{r.overridden ? ` · changed by admin (file says: ${r.fileStatus})` : ''}</small></td>
                  <td><select aria-label={`Status of ${r.schemeCode}`} value={e.status} onChange={ev => change(r, { status: ev.target.value })}>{STATUSES.map(s => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}</select></td>
                  <td><input type="date" aria-label={`Verified date of ${r.schemeCode}`} max={today()} value={e.date} onChange={ev => change(r, { date: ev.target.value })} /></td>
                  <td>{r.criteriaCount}</td>
                  <td className="adminActions">
                    <button type="button" className="primary small" onClick={() => save(r)}>Save</button>
                    <button type="button" className="outline small" onClick={() => save(r, { status: 'active', date: today() })}>Verified today</button>
                    {r.overridden && <button type="button" className="textBtn" onClick={() => revert(r)}>Revert to file</button>}
                    {messages[r.schemeCode] && <p className="matchError">{messages[r.schemeCode]}</p>}
                    {needsAck[r.schemeCode] && <label className="needSave"><input type="checkbox" checked={e.ack} onChange={ev => change(r, { ack: ev.target.checked })} /> I checked the official guideline: this scheme really has only one rule</label>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <h3>Check a new scheme</h3>
      <p className="matchGroupDesc">Paste one scheme as JSON. It is checked against the same schema as schemes.json. Nothing is added; add reviewed schemes to the file itself.</p>
      <textarea className="needText" rows={6} value={json} placeholder='{ "schemeCode": "NEW-001", ... }' onChange={e => setJson(e.target.value)} />
      <button className="primary" onClick={validate} disabled={!json.trim()}>Check scheme</button>
      {validation && (
        <div className={validation.valid ? 'adminResult ok' : 'adminResult bad'}>
          <b>{validation.valid ? 'This scheme is valid.' : 'This scheme has problems:'}</b>
          <ul>{[...validation.errors, ...validation.warnings.map(w => `Note: ${w}`)].map((m, i) => <li key={i}>{m}</li>)}</ul>
        </div>
      )}
    </section>
  );
}
