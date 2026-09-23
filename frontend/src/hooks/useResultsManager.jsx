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
        setLoading(true); setError(null);
        const targetRound = paramRoundId ? await roundService.getById(paramRoundId) : await roundService.getResultRound();
        if (!targetRound) { setError('Nenhuma rodada disponível para consulta de resultados.'); return; }
        const results = await roundService.getResults(targetRound.id);
        setRound(targetRound); setResultsData(results); setStaffList(targetRound.staff || []);
      } catch (err) { setError(err.message || 'Erro ao carregar resultados.'); }
      finally { setLoading(false); }
    };
    loadResults();
  }, [paramRoundId]);

  const getStaffName = useCallback((id) => staffList.find((staff) => staff.id === id)?.name || 'Servidor desconhecido', [staffList]);
  const isPublished = resultsData?.published === true;
  const allocation = resultsData?.allocations?.[0] || null;
  const isAllocated = allocation?.status === 'ALLOCATED';

  return { loading, error, round, isPublished, allocation, isAllocated, getStaffName };
}
