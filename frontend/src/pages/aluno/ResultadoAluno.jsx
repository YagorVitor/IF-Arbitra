import { useParams } from 'react-router-dom';
import { useResultsManager } from '../../hooks/useResultsManager';

import Alert from '../../components/ui/Alert';
import ResultUnpublished from '../../components/ui/ResultUnpublished';
import ResultDetails from '../../components/ui/ResultDetails';

export default function ResultadoAluno() {
  const { roundId: paramRoundId } = useParams();
  
  const {
    loading,
    error,
    round,
    isPublished,
    allocation,
    isAllocated,
    getStaffName
  } = useResultsManager(paramRoundId);

  if (loading) return <div className="p-8 text-center text-gray-500">Carregando resultados...</div>;

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Alert variant="error">{error}</Alert>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Resultado da rodada</h1>

      {!isPublished ? (
        <ResultUnpublished roundName={round?.name} />
      ) : !allocation ? (
        <div className="max-w-4xl">
          <Alert variant="info" title="Sem participação registrada">
            Você não faz parte de nenhum sexteto confirmado nesta rodada.
          </Alert>
        </div>
      ) : (
        <ResultDetails 
          allocation={allocation} 
          isAllocated={isAllocated} 
          getStaffName={getStaffName} 
        />
      )}
    </div>
  );
}