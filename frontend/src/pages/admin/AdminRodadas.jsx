import { useCallback, useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';

const emptyForm = {
  name: '', registration_opens_at: '', registration_closes_at: '',
  preferences_open_at: '', preferences_close_at: '', staff_ids: [], formation_mode: 'TRIOS',
};

function localInput(iso) {
  if (!iso) return '';
  const date = new Date(iso);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

function displayDate(iso) {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

export default function AdminRodadas() {
  const [rounds, setRounds] = useState([]);
  const [staff, setStaff] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [results, setResults] = useState(null);
  const [sextets, setSextets] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const refresh = useCallback(async () => {
    const [roundRows, staffRows] = await Promise.all([adminService.rounds(), adminService.staff()]);
    setRounds(roundRows);
    setStaff(staffRows.filter((person) => person.active !== false));
  }, []);

  useEffect(() => {
    refresh().catch((err) => setError(err.message || 'Falha ao carregar rodadas.')).finally(() => setLoading(false));
  }, [refresh]);

  async function run(action, message) {
    setBusy(true); setError(''); setNotice('');
    try {
      await action();
      await refresh();
      setNotice(message);
    } catch (err) {
      setError(`${err.message || 'Operação não concluída.'}${err.request_id ? ` Código: ${err.request_id}` : ''}`);
    } finally { setBusy(false); }
  }

  function toggleStaff(id) {
    setForm((current) => ({
      ...current,
      staff_ids: current.staff_ids.includes(id)
        ? current.staff_ids.filter((selected) => selected !== id)
        : [...current.staff_ids, id],
    }));
  }

  function startEdit(round) {
    setEditingId(round.id);
    setForm({
      name: round.name,
      formation_mode: round.formation_mode,
      registration_opens_at: localInput(round.registration_opens_at),
      registration_closes_at: localInput(round.registration_closes_at),
      preferences_open_at: localInput(round.preferences_open_at),
      preferences_close_at: localInput(round.preferences_close_at),
      staff_ids: round.staff.map((person) => person.id),
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function saveRound(event) {
    event.preventDefault();
    if (form.staff_ids.length === 0) { setError('Selecione pelo menos um servidor ativo.'); return; }
    const fields = ['registration_opens_at', 'registration_closes_at', 'preferences_open_at', 'preferences_close_at'];
    const payload = { ...form };
    try {
      for (const field of fields) payload[field] = new Date(form[field]).toISOString();
    } catch { setError('Preencha as quatro datas e horários válidos.'); return; }
    await run(async () => {
      if (editingId) await adminService.updateRound(editingId, payload);
      else await adminService.createRound(payload);
      setForm(emptyForm); setEditingId(null);
    }, editingId ? 'Rascunho atualizado.' : 'Rodada criada como rascunho.');
  }

  async function transition(round, action) {
    const labels = { open: 'abrir', publish: 'publicar os resultados de', archive: 'arquivar' };
    if (!window.confirm(`Deseja ${labels[action]} a rodada “${round.name}”?`)) return;
    await run(() => adminService.transitionRound(round.id, action), 'Estado da rodada atualizado.');
  }

  async function allocate(round) {
    if (!window.confirm(`Processar a alocação oficial da rodada “${round.name}”? Confira antes os grupos e preferências; o resultado ficará pronto para publicação.`)) return;
    await run(async () => {
      await adminService.allocate(round.id);
      setSelectedId(round.id);
      setResults(await adminService.results(round.id));
    }, 'Alocação processada. Revise os resultados antes de publicar.');
  }

  async function inspect(round) {
    setBusy(true); setError(''); setSelectedId(round.id);
    try {
      const [resultRows, sextetRows] = await Promise.all([adminService.results(round.id), adminService.sextets(round.id)]);
      setResults(resultRows); setSextets(sextetRows);
    } catch (err) { setError(err.message || 'Não foi possível carregar os detalhes.'); }
    finally { setBusy(false); }
  }

  return (
    <div className="app-page">
      <div className="app-page-head"><div><p className="app-eyebrow">Administração · operação</p><h1 className="app-title">Rodadas</h1><p className="app-subtitle">Prazos e ações são validados pelo servidor. Uma rodada aberta tem prazos e servidores fixos.</p></div><span className="app-pill neutral">{rounds.length} rodadas</span></div>
      {error && <div role="alert" className="p-3 rounded bg-red-50 text-red-800 border border-red-200">{error}</div>}
      {notice && <div role="status" className="p-3 rounded bg-green-50 text-green-800 border border-green-200">{notice}</div>}
      <section className="app-card app-card-pad space-y-4">
        <div className="app-section-head"><div><h2>{editingId ? 'Editar rascunho' : 'Criar rodada'}</h2><p>Defina a janela dos grupos, a janela de preferências e os servidores elegíveis.</p></div></div>
        <form onSubmit={saveRound} className="space-y-4">
          <label className="block text-sm">Nome da rodada<input required minLength={2} maxLength={160} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 block w-full border rounded px-3 py-2" /></label>
          <label className="block text-sm">Formação dos grupos<select value={form.formation_mode} onChange={(e) => setForm({ ...form, formation_mode: e.target.value })} className="mt-1 block w-full border rounded px-3 py-2"><option value="TRIOS">Trios reunidos automaticamente em sextetos</option><option value="SEXTET">Sextetos formados pelos alunos (modo anterior)</option></select></label>
          {form.formation_mode === 'TRIOS' && <p className="text-sm app-muted">Cada servidor recebe dois trios. A seleção começa pela primeira preferência e usa a ordem de confirmação para desempatar. Trios sem par ou vaga ficam pendentes.</p>}
          <div className="grid sm:grid-cols-2 gap-4">
            {[
              ['registration_opens_at', 'Início da confirmação dos grupos'],
              ['registration_closes_at', 'Fim da confirmação dos grupos'],
              ['preferences_open_at', 'Início das preferências'],
              ['preferences_close_at', 'Fim das preferências'],
            ].map(([field, label]) => <label key={field} className="block text-sm">{label}<input required type="datetime-local" value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })} className="mt-1 block w-full border rounded px-3 py-2" /></label>)}
          </div>
          <fieldset className="border rounded p-3"><legend className="text-sm font-semibold px-1">Servidores elegíveis ({form.staff_ids.length})</legend>
            {staff.length === 0 ? <p className="text-sm text-amber-800">Cadastre servidores antes de criar a rodada.</p> : <div className="grid sm:grid-cols-2 gap-2 max-h-64 overflow-auto">
              {staff.map((person) => <label key={person.id} className="text-sm flex items-center gap-2"><input type="checkbox" checked={form.staff_ids.includes(person.id)} onChange={() => toggleStaff(person.id)} />{person.name}</label>)}
            </div>}
          </fieldset>
          <div className="app-actions"><button disabled={busy || staff.length === 0} className="app-button">{editingId ? 'Salvar rascunho' : 'Criar rascunho'}</button>
            {editingId && <button type="button" onClick={() => { setEditingId(null); setForm(emptyForm); }} className="app-button ghost">Cancelar edição</button>}</div>
        </form>
      </section>
      <section className="space-y-3"><h2 className="text-lg font-semibold">Rodadas existentes ({rounds.length})</h2>
        {loading && <p>Carregando...</p>}
        {!loading && rounds.length === 0 && <p className="text-sm text-gray-600">Nenhuma rodada criada.</p>}
        {rounds.map((round) => <article key={round.id} className="app-card app-card-pad space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold text-lg">{round.name}</h3><span className={`app-pill ${round.status === 'OPEN' ? '' : 'neutral'}`}>{({DRAFT:'Rascunho',OPEN:'Aberta',PROCESSED:'Processada',PUBLISHED:'Publicada',ARCHIVED:'Arquivada'})[round.status] || round.status}</span></div>
          <p className="text-sm text-gray-600">{round.formation_mode === 'TRIOS' ? 'Trios' : 'Grupos'}: {round.registered} · Preferências: {round.with_preferences} · Vagas para {round.formation_mode === 'TRIOS' ? 'trios' : 'grupos'}: {round.capacity} · {round.status === 'PROCESSED' || round.status === 'PUBLISHED' || round.status === 'ARCHIVED' ? `Pendentes: ${round.pending}` : `Excedentes: ${round.shortfall}`}</p>
          <p className="text-xs text-gray-600">Grupos: {displayDate(round.registration_opens_at)} a {displayDate(round.registration_closes_at)} · Preferências: {displayDate(round.preferences_open_at)} a {displayDate(round.preferences_close_at)}</p>
          <div className="app-actions pt-1">
            {round.status === 'DRAFT' && <><button disabled={busy} onClick={() => startEdit(round)} className="app-button secondary">Editar</button><button disabled={busy} onClick={() => transition(round, 'open')} className="app-button">Abrir</button></>}
            {round.status === 'OPEN' && <button disabled={busy || !round.can_process} onClick={() => allocate(round)} className="app-button">Processar alocação</button>}
            {round.status === 'PROCESSED' && <button disabled={busy} onClick={() => transition(round, 'publish')} className="app-button">Publicar resultados</button>}
            {round.status === 'PUBLISHED' && <button disabled={busy} onClick={() => transition(round, 'archive')} className="app-button secondary">Arquivar</button>}
            <button disabled={busy} onClick={() => inspect(round)} className="app-button ghost">Ver grupos e resultados</button>
          </div>
          {round.status === 'OPEN' && !round.can_process && <p className="text-xs text-amber-800">O processamento ficará disponível após o encerramento das preferências.</p>}
        </article>)}
      </section>
      {selectedId && <section className="app-card app-card-pad space-y-3">
        <h2 className="text-lg font-semibold">Detalhes da rodada</h2>
        {sextets && <div><h3 className="font-medium">Grupos ({sextets.length})</h3><ol className="list-decimal pl-5 text-sm">{sextets.map((group) => <li key={group.id}>{group.name} · {group.member_count} integrantes · prioridade #{group.priority_sequence}</li>)}</ol></div>}
        {results && <div><h3 className="font-medium">Alocações ({results.allocations.length})</h3><p className="text-xs text-gray-600">{results.published ? 'Publicadas' : 'Ainda não publicadas aos alunos'}</p>{results.allocations.some((item) => item.status === 'UNALLOCATED') && <p className="mt-2 p-3 rounded bg-amber-50 text-amber-900 border border-amber-200">{results.allocations.filter((item) => item.status === 'UNALLOCATED').length} grupo(s) pendente(s). A administração fará o ajuste fora do sistema.</p>}<ol className="list-decimal pl-5 text-sm mt-3 space-y-1">{results.allocations.map((item) => <li key={item.id}>{item.sextet_name}: {item.staff_name || 'Pendente'}{item.partner_trio ? `, junto ao ${item.partner_trio.name}` : ''} ({item.kind === 'REPECHAGE' ? 'repescagem' : 'ranking'})</li>)}</ol></div>}
      </section>}
    </div>
  );
}
