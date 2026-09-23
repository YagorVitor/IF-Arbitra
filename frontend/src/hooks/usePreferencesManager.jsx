import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { roundService } from '../services/roundService';
import { sextetService } from '../services/sextetService';

export function usePreferencesManager(user, paramRoundId) {
  const navigate = useNavigate();
  const [round, setRound] = useState(null);
  const [sextet, setSextet] = useState(null);
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const formatInitialStaffList = (staff, savedPreferences) => {
    if (!staff) return [];
    if (!savedPreferences?.length) return staff;
    return [...staff].sort((a, b) => {
      const idxA = savedPreferences.indexOf(a.id); const idxB = savedPreferences.indexOf(b.id);
      if (idxA === -1) return 1; if (idxB === -1) return -1; return idxA - idxB;
    });
  };

  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true);
        const targetRound = paramRoundId ? await roundService.getById(paramRoundId) : await roundService.getPreferencesRound();
        if (!targetRound) { setError('Nenhuma rodada disponível para envio de preferências.'); return; }
        const sextetData = await roundService.getMySextet(targetRound.id);
        if (!sextetData) { navigate('/aluno'); return; }
        setRound(targetRound); setSextet(sextetData); setStaffList(formatInitialStaffList(targetRound.staff, sextetData.preferences));
      } catch (err) { setError(err.message || 'Não foi possível carregar as preferências.'); }
      finally { setLoading(false); }
    };
    loadPreferences();
  }, [paramRoundId, navigate]);

  const moveUp = useCallback((index) => { if (index === 0) return; setStaffList((prev) => { const next = [...prev]; [next[index - 1], next[index]] = [next[index], next[index - 1]]; return next; }); }, []);
  const moveDown = useCallback((index) => { setStaffList((prev) => { if (index === prev.length - 1) return prev; const next = [...prev]; [next[index + 1], next[index]] = [next[index], next[index + 1]]; return next; }); }, []);
  const isLeader = sextet?.members?.[0]?.id === user?.id;

  const handleSave = async () => {
    if (!sextet || !isLeader || !round?.preferences_open) return;
    try {
      setSaving(true); setError(null);
      const responseData = await sextetService.updatePreferences(sextet.id, { staff_ids: staffList.map((staff) => staff.id), expected_version: sextet.preference_version });
      setSextet((prev) => ({ ...prev, preference_version: responseData.version }));
      navigate(`/aluno${round.id ? `?roundId=${round.id}` : ''}`);
    } catch (err) {
      if (err.code === 'PREFERENCE_VERSION_CONFLICT') setError('As preferências foram alteradas em outra aba. Recarregue a página antes de salvar.');
      else if (err.code === 'PREFERENCE_WINDOW_CLOSED') setError('A janela de preferências foi encerrada.');
      else setError(err.message || 'Erro ao salvar preferências.');
    } finally { setSaving(false); }
  };

  return { round, sextet, staffList, loading, saving, error, isLeader, moveUp, moveDown, handleSave };
}
