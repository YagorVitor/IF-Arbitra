import { useState, useEffect, useCallback } from 'react';
import { roundService } from '../services/roundService';

export function useResultsManager(paramRoundId) {
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
        setStaffList(roundInfo.staff || []);

      } catch (err) {
        setError(err.message || 'Erro ao carregar resultados.');
      } finally {
        setLoading(false);
      }
    };

    loadResults();
  }, [paramRoundId]);

  const getStaffName = useCallback((id) => {
    return staffList.find(s => s.id === id)?.name || 'Servidor desconhecido';
  }, [staffList]);

  const isPublished = resultsData?.published === true;
  const allocation = resultsData?.allocations?.[0] || null;
  const isAllocated = allocation?.status === 'ALLOCATED';

  return {
    loading,
    error,
    round,
    isPublished,
    allocation,
    isAllocated,
    getStaffName
  };
}