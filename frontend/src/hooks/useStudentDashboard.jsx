import { useState, useEffect } from 'react';
import { roundService } from '../services/roundService';
import { format, isValid } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export function useStudentDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [round, setRound] = useState(null);
  const [group, setGroup] = useState(null);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        const activeRound = await roundService.getActiveRound();
        
        if (!activeRound) { setRound(null); setGroup(null); return; }

        const groupData = await roundService.getMyGroup(activeRound.id);

        setRound(activeRound);
        setGroup(groupData && groupData.id ? groupData : null);
      } catch (err) {
        setError(err.message || 'Erro ao carregar dados do painel.');
      } finally { setLoading(false); }
    }

    loadDashboardData();
  }, []);

  const getCurrentStage = () => {
    if (!round) return 1;
    if (round.status === 'PUBLISHED' || round.status === 'ARCHIVED') return 4;
    if (round.status === 'PROCESSED' || (round.status === 'OPEN' && !round.registration_open && !round.preferences_open)) return 3;
    if (group && round.preferences_open) return 2;
    return 1;
  };

  const getDeadlineText = () => {
    if (!round) return '';
    const deadline = round.registration_open && !group ? round.registration_closes_at : round.preferences_open ? round.preferences_close_at : null;
    if (deadline && isValid(new Date(deadline))) return `Encerra em ${format(new Date(deadline), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}`;
    if (round.status === 'PROCESSED') return 'Aguardando publicação';
    if (round.status === 'PUBLISHED') return 'Resultados disponíveis';
    if (round.status === 'ARCHIVED') return 'Rodada arquivada';
    return round.status === 'DRAFT' ? 'Aguardando abertura' : 'Aguardando processamento';
  };

  return {
    loading,
    error,
    round,
    group,
    currentStage: getCurrentStage(),
    deadlineText: getDeadlineText(),
  };
}
