import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { roundService } from '../../services/roundService';
import Alert from '../../components/ui/Alert';
import Button from '../../components/ui/Button';

export default function ResultadoAluno() {
  const { roundId: paramRoundId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [round, setRound] = useState(null);
  const [resultsData, setResultsData] = useState(null);
  const [staffList, setStaffList] = useState([]);

  useEffect(() => {
    const loadResults = async () => {
      try {
        setLoading(true);
        
        let targetRoundId = paramRoundId;
        if (!targetRoundId) {
          const activeRound = await roundService.getActiveRound();
          if (!activeRound) {
            setError('Nenhuma rodada encontrada.');
            return;
          }
          targetRoundId = activeRound.id;
        }

        const [roundInfo, results] = await Promise.all([
          roundService.getById(targetRoundId),
          roundService.getResults(targetRoundId)
        ]);

        setRound(roundInfo);
        setResultsData(results);
        setStaffList(roundInfo.staff);

      } catch (err) {
        setError(err.message || 'Erro ao carregar resultados.');
      } finally {
        setLoading(false);
      }
    };

    loadResults();
  }, [paramRoundId]);

  if (loading) return <div className="p-8 text-center text-gray-500">Carregando resultados...</div>;

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Alert variant="error">{error}</Alert>
      </div>
    );
  }

  // Estado 1: Resultados ainda não foram publicados
  if (!resultsData?.published) {
    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Resultado da rodada</h1>
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center flex flex-col items-center">
          <Clock className="w-12 h-12 text-blue-500 mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Resultados em processamento</h2>
          <p className="text-gray-600 mb-6 max-w-md">
            A alocação para a rodada "{round?.name}" ainda não foi publicada pela administração. Volte mais tarde.
          </p>
          <Button onClick={() => navigate('/aluno')} variant="outline">
            Voltar ao Início
          </Button>
        </div>
      </div>
    );
  }

  // Se publicado, o array terá 0 ou 1 item para o aluno
  const allocation = resultsData.allocations?.[0];

  // Estado 2: Aluno sem sexteto na rodada
  if (!allocation) {
    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Resultado da rodada</h1>
        <Alert variant="info" title="Sem participação registrada">
          Você não faz parte de nenhum sexteto confirmado nesta rodada.
        </Alert>
      </div>
    );
  }

  const isAllocated = allocation.status === 'ALLOCATED';

  // Função auxiliar para mapear UUID do ranking para nome do servidor
  const getStaffName = (id) => staffList.find(s => s.id === id)?.name || 'Servidor desconhecido';

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Resultado da rodada</h1>

      {/* Cartão de Status Principal */}
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
        {/* Detalhes do Sexteto */}
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

        {/* Ranking Enviado */}
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
    </div>
  );
}