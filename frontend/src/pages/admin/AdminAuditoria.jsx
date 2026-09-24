import { useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';

export default function AdminAuditoria() {
  const [events, setEvents] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load(beforeId) {
    setLoading(true);
    setError('');
    try {
      const page = await adminService.audit(beforeId);
      setEvents((previous) => beforeId ? [...previous, ...page.events] : page.events);
      setCursor(page.next_cursor);
    } catch (err) {
      setError(`${err.message || 'Falha ao carregar auditoria.'}${err.request_id ? ` Código: ${err.request_id}` : ''}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(null); }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <div><h1 className="text-2xl font-bold">Auditoria</h1><p className="text-sm text-gray-600 mt-1">Eventos mais recentes primeiro. O código de atendimento permite localizar uma requisição específica.</p></div>
      {error && <p role="alert" className="bg-red-50 text-red-800 border border-red-200 p-3 rounded">{error}</p>}
      <button type="button" disabled={loading} onClick={() => load(null)} className="border rounded px-3 py-2 text-sm disabled:opacity-50">Atualizar</button>
      <div className="space-y-2">
        {events.map((event) => <details key={event.id} className="border rounded p-3 text-sm">
          <summary className="cursor-pointer flex flex-wrap gap-x-4 gap-y-1">
            <span className="font-medium">#{event.id} · {event.event_type}</span>
            <span>{new Date(event.occurred_at).toLocaleString('pt-BR')}</span>
            <span>{event.actor_name || 'Sistema'}</span>
          </summary>
          <div className="mt-3 space-y-1 text-gray-700 break-all">
            <p>Entidade: {event.entity_type || '—'} · {event.entity_id || '—'}</p>
            <p>Código da requisição: {event.request_id}</p>
            <pre className="bg-gray-50 p-2 rounded overflow-auto whitespace-pre-wrap">{JSON.stringify({ payload: event.payload, previous_state: event.previous_state, resulting_state: event.resulting_state }, null, 2)}</pre>
          </div>
        </details>)}
        {!loading && events.length === 0 && <p className="text-sm text-gray-600">Nenhum evento encontrado.</p>}
      </div>
      {cursor && <button type="button" disabled={loading} onClick={() => load(cursor)} className="border rounded px-3 py-2 text-sm disabled:opacity-50">{loading ? 'Carregando...' : 'Carregar mais'}</button>}
    </div>
  );
}
