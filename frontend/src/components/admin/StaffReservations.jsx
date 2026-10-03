import { useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';

export default function StaffReservations({ students, staff }) {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ captain_id: '', staff_id: '', reason: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  useEffect(() => {
    let cancelled = false;
    adminService.reservations().then((data) => { if (!cancelled) setRows(data); })
      .catch((err) => { if (!cancelled) setError(err.message || 'Não foi possível carregar as reservas.'); });
    return () => { cancelled = true; };
  }, []);
  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await adminService.setReservation(form.captain_id, { staff_id: form.staff_id || null, reason: form.reason.trim() });
      setRows(await adminService.reservations());
      setForm({ captain_id: '', staff_id: '', reason: '' });
      setNotice('Reserva atualizada. As execuções já concluídas mantêm seus resultados.');
    } catch (err) {
      setError(err.message || 'Não foi possível atualizar a reserva.');
    } finally { setBusy(false); }
  }
  return <section className="app-card app-card-pad space-y-4">
    <div><p className="app-eyebrow">Restrito à administração</p><h2 className="text-lg font-semibold">Reservas de servidores</h2>
      <p className="text-sm app-muted">Valem nas próximas alocações de grupos, enquanto esta configuração existir. Sem grupo confirmado, o servidor fica disponível. As execuções preservam a configuração usada.</p></div>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {notice && <p role="status" className="text-green-700">{notice}</p>}
    {rows.length === 0 ? <p className="text-sm app-muted">Nenhuma reserva cadastrada.</p> : <ul className="space-y-3">{rows.map((row) => <li key={row.captain_id} className="border rounded p-3 text-sm">
      <div className="flex flex-wrap justify-between gap-2"><strong>{row.captain_name} · {row.staff_name}</strong><button type="button" className="text-green-700" disabled={busy} onClick={() => setForm({ captain_id: row.captain_id, staff_id: row.staff_id, reason: row.reason })}>Editar reserva</button></div>
      <p className="mt-1 break-words">{row.reason}</p>{!row.enabled && <p className="text-amber-800">Inativa: revise o cadastro do capitão ou servidor.</p>}
    </li>)}</ul>}
    <form onSubmit={save} className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2">
        <label className="text-sm">Capitão<select required disabled={busy} className="border rounded px-3 py-2 w-full mt-1" value={form.captain_id} onChange={(event) => setForm({ ...form, captain_id: event.target.value })}><option value="">Selecione o capitão</option>{students.filter((student) => (student.is_captain && !student.removed_at) || rows.some((row) => row.captain_id === student.id)).map((student) => <option key={student.id} value={student.id}>{student.name}</option>)}</select></label>
        <label className="text-sm">Servidor reservado<select disabled={busy} className="border rounded px-3 py-2 w-full mt-1" value={form.staff_id} onChange={(event) => setForm({ ...form, staff_id: event.target.value })}><option value="">Sem reserva (remover)</option>{staff.filter((person) => person.active !== false || rows.some((row) => row.staff_id === person.id)).map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}</select></label>
      </div>
      <label className="block text-sm">Justificativa administrativa<textarea required minLength={10} maxLength={1000} className="border rounded px-3 py-2 w-full mt-1" rows={2} value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })}/></label>
      <button disabled={busy || !form.captain_id || form.reason.trim().length < 10} className="app-button secondary">{busy ? 'Salvando...' : 'Salvar reserva'}</button>
    </form>
  </section>;
}
