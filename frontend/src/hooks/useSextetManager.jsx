import { useState, useEffect } from 'react';
import { roundService } from '../services/roundService';
import { studentService } from '../services/studentService';

export function useSextetManager(currentUser, initialRoundId) {
  const [roundId, setRoundId] = useState(initialRoundId || null);
  const [existingSextet, setExistingSextet] = useState(null);
  const [isOccupiedGlobally, setIsOccupiedGlobally] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Resolve a rodada ativa
  useEffect(() => {
    async function resolveRound() {
      if (initialRoundId) return;
      try {
        const openRound = await roundService.getActiveRound();
        if (openRound) setRoundId(openRound.id);
        else setError('Nenhuma rodada disponível de momento.');
      } catch (err) {
        setError(err.message || 'Erro ao carregar rodadas.');
      }
    }
    resolveRound();
  }, [initialRoundId]);

  // Busca o sexteto ou verifica bloqueio global
  useEffect(() => {
    async function fetchMySextet() {
      if (!roundId || !currentUser?.login) return;
      setIsLoading(true);
      setError('');

      try {
        const sextetData = await roundService.getMySextet(roundId);
        if (sextetData && sextetData.id) {
          setExistingSextet(sextetData);
        } else {
          setExistingSextet(null);
          const students = await studentService.search(currentUser.login);
          const me = students.find(s => s.login.toLowerCase() === currentUser.login.toLowerCase());
          if (me && me.occupied) setIsOccupiedGlobally(true);
        }
      } catch (err) {
        setError(err.message || 'Erro ao verificar sexteto existente.');
      } finally {
        setIsLoading(false);
      }
    }
    fetchMySextet();
  }, [roundId, currentUser?.login]);

  // Submissão do sexteto
  const submitSextet = async (memberIds) => {
    setIsSubmitting(true);
    setError('');
    try {
      const payload = {
        name: `Sexteto de ${currentUser.name.split(' ')[0]}`,
        members: memberIds,
        idempotency_key: crypto.randomUUID(),
      };
      const createdSextet = await roundService.createSextet(roundId, payload);
      setExistingSextet(createdSextet);
    } catch (err) {
      setError(err.message || 'Falha ao confirmar o sexteto.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    existingSextet,
    isOccupiedGlobally,
    isLoading,
    isSubmitting,
    error,
    setError,
    submitSextet
  };
}