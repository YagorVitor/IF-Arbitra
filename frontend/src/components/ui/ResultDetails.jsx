import { CheckCircle, XCircle, Landmark, UsersRound } from 'lucide-react';

export default function ResultDetails({ allocation, isAllocated, getStaffName }) {
  const trace = allocation.trace || {};
  const ranking = trace.ranking || [];
  const priority = trace.priority_sequence;
  const isRepechage = allocation.kind === 'REPECHAGE';

  return (
    <>
      <div className={`app-hero-result ${!isAllocated ? 'bg-red-50 border-red-200' : ''}`}>
        {isAllocated ? <CheckCircle className="w-8 h-8 text-green-600 shrink-0" /> : <XCircle className="w-8 h-8 text-red-600 shrink-0" />}
        <div>
          <span className="app-label">{isAllocated ? 'Servidor alocado' : 'Sexteto não alocado'}</span>
          {isAllocated ? <><h2>{allocation.staff_name || getStaffName(allocation.staff_id)}</h2><p><Landmark size={15} className="inline mr-1"/>Sua preferência: {allocation.preference_position ? `${allocation.preference_position}ª` : 'repescagem'}</p></> : <><h2>Capacidade esgotada</h2><p>Não foi possível alocar um servidor para o seu sexteto nesta rodada.</p></>}
        </div>
      </div>

      <div className="app-grid-2">
        <div className="app-card app-card-pad"><div className="app-section-head"><div><h3>Seu sexteto</h3><p>Detalhes da participação.</p></div><UsersRound size={19} className="text-green-700"/></div><div className="space-y-4 text-sm"><div><p className="app-label">Nome do grupo</p><p className="font-semibold">{allocation.sextet_name || 'Não informado'}</p></div><div><p className="app-label">Prioridade na alocação</p><p className="font-semibold">{priority != null ? `#${priority}` : 'Não informado'}</p></div><div><p className="app-label">Tipo de participação</p><p className="font-semibold">{isRepechage ? 'Repescagem (sem ranking)' : 'Principal (com ranking)'}</p></div></div></div>
        <div className="app-card app-card-pad"><div className="app-section-head"><div><h3>Ranking processado</h3><p>Ordem considerada na alocação.</p></div></div>{ranking.length > 0 ? <ol className="space-y-3">{ranking.map((staffId, index) => { const isChosen = staffId === trace.chosen; return <li key={staffId} className="flex items-center gap-3 text-sm"><span className="app-rank">{String(index+1).padStart(2,'0')}</span><span className={`${isChosen ? 'font-bold text-green-700' : 'text-gray-700'}`}>{getStaffName(staffId)}</span>{isChosen && <CheckCircle className="w-4 h-4 text-green-600 ml-auto" />}</li>; })}</ol> : <p className="text-sm app-muted">Nenhum ranking foi enviado por este sexteto.</p>}</div>
      </div>
    </>
  );
}
