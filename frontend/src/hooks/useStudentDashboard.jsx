import { useState, useEffect } from 'react';
import { roundService } from '../services/roundService';
import { format, isValid } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export function useStudentDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [round, setRound] = useState(null);
  const [sextet, setSextet] = useState(null);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        const activeRound = await roundService.getActiveRound();
        
        if (!activeRound) { setRound(null); setSextet(null); return; }

        const sextetData = await roundService.getMySextet(activeRound.id);

        setRound(activeRound);
        setSextet(sextetData && sextetData.id ? sextetData : null);
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
    if (sextet && round.preferences_open) return 2;
    return 1;
  };

  const getDeadlineText = () => {
    if (!round) return '';
    const deadline = round.registration_open && !sextet ? round.registration_closes_at : round.preferences_open ? round.preferences_close_at : null;
    if (deadline && isValid(new Date(deadline))) return `Encerra em ${format(new Date(deadline), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}`;
    return round.status === 'DRAFT' ? 'Aguardando abertura' : 'Etapa encerrada';
  };

  return {
    loading,
    error,
    round,
    sextet,
    currentStage: getCurrentStage(),
    deadlineText: getDeadlineText(),
  };
}
