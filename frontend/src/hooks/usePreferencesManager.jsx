import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { roundService } from '../services/roundService';
import { sextetService } from '../services/sextetService';

export function usePreferencesManager(user, paramRoundId) {
  const navigate = useNavigate();
  const [sextet, setSextet] = useState(null);
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const formatInitialStaffList = (staff, savedPreferences) => {
    if (!staff) return [];
    if (!savedPreferences || savedPreferences.length === 0) return staff;

    return [...staff].sort((a, b) => {
      const idxA = savedPreferences.indexOf(a.id);
      const idxB = savedPreferences.indexOf(b.id);
      if (idxA === -1) return 1;
      if (idxB === -1) return -1;
      return idxA - idxB;
    });
  };

  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true);

        const targetRound = paramRoundId
          ? await roundService.getById(paramRoundId)
          : await roundService.getActiveRound();

        if (!targetRound) {
          setError('Nenhuma rodada ativa encontrada no momento.');
          return;
        }

        const sextetData = await roundService.getMySextet(targetRound.id);

        if (!sextetData) {
          navigate('/aluno');
          return;
        }

        setSextet(sextetData);
        setStaffList(formatInitialStaffList(targetRound.staff, sextetData.preferences));
      } catch (err) {
        setError(err.message || 'Não foi possível carregar as preferências.');
      } finally {
        setLoading(false);
      }
    };

    loadPreferences();
  }, [paramRoundId, navigate]);

  const moveUp = useCallback((index) => {
    if (index === 0) return;
    setStaffList((prev) => {
      const newList = [...prev];
      [newList[index - 1], newList[index]] = [newList[index], newList[index - 1]];
      return newList;
    });
  }, []);

  const moveDown = useCallback((index) => {
    setStaffList((prev) => {
      if (index === prev.length - 1) return prev;
      const newList = [...prev];
      [newList[index + 1], newList[index]] = [newList[index], newList[index + 1]];
      return newList;
    });
  }, []);

  const isLeader = sextet?.members?.[0]?.id === user?.id;

  const handleSave = async () => {
    if (!sextet || !isLeader) return;

    try {
      setSaving(true);
      setError(null);

      const payload = {
        staff_ids: staffList.map((staff) => staff.id),
        expected_version: sextet.preference_version,
      };

      const responseData = await sextetService.updatePreferences(sextet.id, payload);

      setSextet((prev) => ({ ...prev, preference_version: responseData.version }));
      navigate('/aluno');
    } catch (err) {
      if (err.code === 'PREFERENCE_VERSION_CONFLICT') {
        setError('As preferências foram alteradas em outra aba. Recarregue a página antes de salvar.');
      } else {
        setError(err.message || 'Erro ao salvar preferências.');
      }
    } finally {
      setSaving(false);
    }
  };

  return {
    sextet,
    staffList,
    loading,
    saving,
    error,
    isLeader,
    moveUp,
    moveDown,
    handleSave,
  };
}