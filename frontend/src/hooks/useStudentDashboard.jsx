import { useState, useEffect } from 'react';
import { roundService } from '../services/roundService';

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
        
        if (!activeRound) {
          setError('Nenhuma rodada ativa no momento.');
          return;
        }

        const sextetData = await roundService.getMySextet(activeRound.id);

        setRound(activeRound);
        setSextet(sextetData && sextetData.id ? sextetData : null);
      } catch (err) {
        setError(err.message || 'Erro ao carregar dados do painel.');
      } finally {
        setLoading(false); // Corrigido de setIsLoading para setLoading
      }
    }

    loadDashboardData();
  }, []);

  const getCurrentStage = () => {
    if (!round) return 1;
    if (round.status === 'PUBLISHED' || round.status === 'ARCHIVED') return 4;
    if (round.status === 'PROCESSED' || (!round.registration_open && !round.preferences_open)) return 3;
    if (sextet && round.preferences_open) return 2;
    return 1;
  };

  const getDeadlineText = () => {
    if (!round) return '';
    if (round.registration_open && !sextet) {
      return `Encerra em ${new Date(round.registration_closes_at).toLocaleDateString('pt-BR')} às ${new Date(round.registration_closes_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
    }
    if (round.preferences_open) {
      return `Encerra em ${new Date(round.preferences_close_at).toLocaleDateString('pt-BR')} às ${new Date(round.preferences_close_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
    }
    return 'Etapa encerrada';
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