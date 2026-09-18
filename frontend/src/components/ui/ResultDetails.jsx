import { CheckCircle, XCircle } from 'lucide-react';

export default function ResultDetails({ allocation, isAllocated, getStaffName }) {
  return (
    <>
      <div className={`p-6 rounded-lg border ${isAllocated ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'} flex items-start gap-4`}>
        {isAllocated ? (
          <CheckCircle className="w-8 h-8 text-green-600 shrink-0" />
        ) : (
          <XCircle className="w-8 h-8 text-red-600 shrink-0" />
        )}
        
        <div>
          <h2 className={`text-xs font-bold uppercase tracking-wider mb-1 ${isAllocated ? 'text-green-800' : 'text-red-800'}`}>
            {isAllocated ? 'Servidor Alocado' : 'Não Alocado'}
          </h2>
          {isAllocated ? (
            <>
              <p className="text-2xl font-bold text-gray-900">{allocation.staff_name}</p>
              <p className="text-green-700 font-medium mt-1">Sua preferência: {allocation.preference_position}ª</p>
            </>
          ) : (
            <>
              <p className="text-2xl font-bold text-gray-900">Capacidade esgotada</p>
              <p className="text-red-700 font-medium mt-1">Não foi possível alocar um servidor para o seu sexteto nesta rodada.</p>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wide border-b border-gray-100 pb-3 mb-4">
            Detalhes do Sexteto
          </h3>
          <div className="space-y-4 text-sm">
            <div>
              <p className="text-gray-500 mb-1">Nome do grupo</p>
              <p className="font-semibold text-gray-900">{allocation.sextet_name}</p>
            </div>
            <div>
              <p className="text-gray-500 mb-1">Prioridade na alocação</p>
              <p className="font-semibold text-gray-900">#{allocation.trace.priority_sequence}</p>
            </div>
            <div>
              <p className="text-gray-500 mb-1">Tipo de participação</p>
              <p className="font-semibold text-gray-900">
                {allocation.kind === 'MAIN' ? 'Principal (Com ranking)' : 'Repescagem (Sem ranking)'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wide border-b border-gray-100 pb-3 mb-4">
            Ranking Processado
          </h3>
          {allocation.trace.ranking && allocation.trace.ranking.length > 0 ? (
            <ul className="space-y-3">
              {allocation.trace.ranking.map((staffId, index) => {
                const isChosen = staffId === allocation.trace.chosen;
                return (
                  <li key={staffId} className="flex items-center gap-3 text-sm">
                    <span className="w-5 text-gray-400 font-medium">{index + 1}.</span>
                    <span className={`${isChosen ? 'font-bold text-green-700' : 'text-gray-700'}`}>
                      {getStaffName(staffId)}
                    </span>
                    {isChosen && <CheckCircle className="w-4 h-4 text-green-600 ml-auto" />}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 italic">Nenhum ranking foi enviado por este sexteto.</p>
          )}
        </div>
      </div>
    </>
  );
}