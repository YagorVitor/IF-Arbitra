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
    <div className="app-page">
      <div className="app-page-head"><div><p className="app-eyebrow">Administração · rastreabilidade</p><h1 className="app-title">Auditoria</h1><p className="app-subtitle">Eventos mais recentes primeiro. O código de atendimento permite localizar uma requisição específica.</p></div><span className="app-pill neutral">{events.length} eventos</span></div>
      {error && <p role="alert" className="bg-red-50 text-red-800 border border-red-200 p-3 rounded">{error}</p>}
      <div><button type="button" disabled={loading} onClick={() => load(null)} className="app-button secondary">Atualizar</button></div>
      <div className="space-y-2">
        {events.map((event) => <details key={event.id} className="app-card app-card-pad text-sm">
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
      {cursor && <div><button type="button" disabled={loading} onClick={() => load(cursor)} className="app-button secondary">{loading ? 'Carregando...' : 'Carregar mais'}</button></div>}
    </div>
  );
}
