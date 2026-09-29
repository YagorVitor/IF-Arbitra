import { useParams } from 'react-router-dom';
import { useResultsManager } from '../../hooks/useResultsManager';

import Alert from '../../components/ui/Alert';
import ResultUnpublished from '../../components/ui/ResultUnpublished';
import ResultDetails from '../../components/ui/ResultDetails';
import EmptyRoundState from '../../components/ui/EmptyRoundState';

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

  if (loading) return <div className="app-card app-card-pad" role="status">Carregando resultados...</div>;
  if (!round && !error) return <EmptyRoundState section="resultado" />;

  if (error) {
    return (
      <div className="app-page">
        <Alert variant="error">{error}</Alert>
      </div>
    );
  }

  const trioMode = round?.formation_mode === 'TRIOS';

  return (
    <div className="app-page">
      <div className="app-page-head"><div><p className="app-eyebrow">Resultado · {round?.name}</p><h1 className="app-title">Resultado da rodada</h1><p className="app-subtitle">Acompanhe a alocação do seu {trioMode ? 'trio' : 'grupo registrado'} e a ordem processada.</p></div>{isPublished && <span className="app-pill">Publicado</span>}</div>

      {!isPublished ? (
        <ResultUnpublished roundName={round?.name} />
      ) : !allocation ? (
        <div className="max-w-4xl">
          <Alert variant="info" title="Sem participação registrada">
            Você não faz parte de nenhum grupo confirmado nesta rodada.
          </Alert>
        </div>
      ) : (
        <ResultDetails 
          allocation={allocation} 
          isAllocated={isAllocated} 
          getStaffName={getStaffName} 
          trioMode={trioMode}
        />
      )}
    </div>
  );
}
