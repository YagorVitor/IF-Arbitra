import { useState } from 'react';
import { UsersRound, Save } from 'lucide-react';

export default function AssignmentEditor({ round, results, groups, busy, onSave }) {
  const [draft, setDraft] = useState(() => Object.fromEntries(results.allocations.map((item) => [item.id, item.staff_id || ''])));
  const [reason, setReason] = useState('');
  const editable = ['PROCESSED', 'PUBLISHED'].includes(round.status);
  const capacity = round.formation_mode === 'TRIOS' ? 2 : 1;
  const occupancy = Object.values(draft).reduce((counts, id) => {
    if (id) counts[id] = (counts[id] || 0) + 1;
    return counts;
  }, {});
  const pending = Object.values(draft).filter((id) => !id).length;
  const exceeded = Object.values(occupancy).some((count) => count > capacity);
  const changed = results.allocations.some((item) => draft[item.id] !== (item.staff_id || ''));
  const groupById = Object.fromEntries((groups || []).map((group) => [group.id, group]));

  function submit(event) {
    event.preventDefault();
    onSave({
      expected_revision: results.revision || 0,
      reason: reason.trim(),
      assignments: results.allocations.map((item) => ({ allocation_id: item.id, staff_id: draft[item.id] || null })),
    });
  }

  return <form onSubmit={submit} className="space-y-4">
    <div className="app-section-head"><div><h3>Atribuições dos grupos</h3><p>{editable ? 'Resolva pendências ou reorganize os grupos. Respeite a capacidade de cada servidor.' : round.status === 'ARCHIVED' ? 'Esta rodada está arquivada. Consulte as atribuições registradas.' : 'As atribuições estarão disponíveis após o processamento.'}</p></div><span className={`app-pill ${pending ? 'neutral' : ''}`}>{pending} pendentes</span></div>
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {round.staff.map((person) => <div key={person.id} className={`rounded-lg border p-3 text-sm ${occupancy[person.id] > capacity ? 'border-red-300 bg-red-50' : 'border-green-100 bg-green-50/50'}`}><p className="font-semibold">{person.name}</p><p className="app-muted">{occupancy[person.id] || 0} de {capacity} {round.formation_mode === 'TRIOS' ? 'trios' : 'grupo'}</p></div>)}
    </div>
    {results.allocations.length === 0 && <p className="text-sm app-muted">Nenhuma alocação processada nesta rodada.</p>}
    <div className="space-y-3">
      {results.allocations.map((item) => {
        const group = groupById[item.sextet_id];
        const partner = results.allocations.find((other) => other.id !== item.id && draft[item.id] && draft[other.id] === draft[item.id]);
        return <article key={item.id} className="rounded-xl border border-gray-200 p-4 grid gap-4 md:grid-cols-2">
          <div><div className="flex gap-2 items-center"><UsersRound size={18} className="text-green-700"/><h4 className="font-semibold">{item.sextet_name}</h4></div><p className="mt-1 text-xs app-muted">Prioridade #{item.trace.priority_sequence}{item.manually_adjusted ? ' · Ajuste administrativo' : ''}</p><ul className="mt-2 text-sm space-y-1">{group?.members?.map((member) => <li key={member.id}>{member.name}{member.id === group.leader_id ? ' · Capitão' : ''}</li>)}</ul></div>
          <div><label className="block text-sm font-medium" htmlFor={`assignment-${item.id}`}>Servidor</label><select id={`assignment-${item.id}`} disabled={!editable || busy} value={draft[item.id]} onChange={(event) => setDraft({ ...draft, [item.id]: event.target.value })} className="mt-1 w-full rounded-lg border px-3 py-3 bg-white"><option value="">Manter pendente</option>{round.staff.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}</select><p className="mt-2 text-xs app-muted">{partner ? `Junto ao ${partner.sextet_name}` : draft[item.id] ? 'Grupo atribuído a este servidor.' : 'Aguardando atribuição.'}</p></div>
        </article>;
      })}
    </div>
    {results.adjustment_reason && <p className="text-sm app-muted">Última justificativa: {results.adjustment_reason}</p>}
    {editable && results.allocations.length > 0 && <>
      {exceeded && <p role="alert" className="text-sm text-red-700">Há servidor acima da capacidade. Redistribua os grupos antes de salvar.</p>}
      <label className="block text-sm font-medium">Justificativa do ajuste<textarea required minLength={10} maxLength={1000} value={reason} onChange={(event) => setReason(event.target.value)} rows={3} className="mt-1 w-full border rounded-lg px-3 py-2" placeholder="Explique a escolha do servidor ou a reorganização dos grupos."/></label>
      <p className="text-sm app-muted">{results.published ? 'Ao salvar, os alunos verão as novas atribuições nos resultados publicados.' : 'Os alunos verão as atribuições quando você publicar os resultados.'} A alocação automática e cada ajuste ficam registrados na auditoria.</p>
      <button type="submit" className="app-button" disabled={busy || !changed || exceeded || reason.trim().length < 10}><Save size={16}/>{busy ? 'Salvando...' : 'Salvar ajustes'}</button>
    </>}
  </form>;
}
