import { useState, useEffect } from 'react';
import { roundService } from '../services/roundService';
import { studentService } from '../services/studentService';

export function useSextetManager(currentUser, initialRoundId) {
  const [roundId, setRoundId] = useState(initialRoundId || null);
  const [round, setRound] = useState(null);
  const [existingSextet, setExistingSextet] = useState(null);
  const [isOccupiedGlobally, setIsOccupiedGlobally] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function resolveRound() {
      if (initialRoundId) { setRoundId(initialRoundId); return; }
      try {
        const openRound = await roundService.getRegistrationRound();
        if (openRound) { setRound(openRound); setRoundId(openRound.id); }
        else { setError('Não há uma rodada aberta para confirmação de sextetos.'); setIsLoading(false); }
      } catch (err) { setError(err.message || 'Erro ao carregar rodadas.'); setIsLoading(false); }
    }
    resolveRound();
  }, [initialRoundId]);

  useEffect(() => {
    async function fetchMySextet() {
      if (!roundId || !currentUser?.login) return;
      setIsLoading(true); setError('');
      try {
        const [roundData, sextetData] = await Promise.all([
          roundService.getById(roundId),
          roundService.getMySextet(roundId),
        ]);
        setRound(roundData);
        if (sextetData?.id) setExistingSextet(sextetData);
        else {
          setExistingSextet(null);
          const students = await studentService.search(currentUser.login);
          const me = students.find((s) => s.login.toLowerCase() === currentUser.login.toLowerCase());
          setIsOccupiedGlobally(Boolean(me?.occupied));
        }
      } catch (err) { setError(err.message || 'Erro ao verificar sexteto existente.'); }
      finally { setIsLoading(false); }
    }
    fetchMySextet();
  }, [roundId, currentUser?.login]);

  const submitSextet = async (memberIds) => {
    if (!round?.registration_open) { setError('A janela de confirmação desta rodada está encerrada.'); return; }
    setIsSubmitting(true); setError('');
    try {
      const payload = { name: `Sexteto de ${currentUser.name.split(' ')[0]}`, members: memberIds, idempotency_key: crypto.randomUUID() };
      const createdSextet = await roundService.createSextet(roundId, payload);
      setExistingSextet(createdSextet);
    } catch (err) {
      const messages = { INTEGRITY_CONFLICT: 'Um dos integrantes já pertence a outro sexteto ativo.', REGISTRATION_WINDOW_CLOSED: 'A janela de confirmação desta rodada foi encerrada.', IDEMPOTENCY_CONFLICT: 'Esta confirmação já foi usada com outra composição.', INVALID_SEXTET_COMPOSITION: 'Todos os seis integrantes devem ser alunos ativos.', DUPLICATE_MEMBER: 'Selecione seis alunos diferentes.' };
      setError(messages[err.code] || err.message || 'Falha ao confirmar o sexteto.');
    } finally { setIsSubmitting(false); }
  };

  return { round, existingSextet, isOccupiedGlobally, isLoading, isSubmitting, error, setError, submitSextet };
}
