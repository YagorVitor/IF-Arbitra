import { useState, useEffect, useRef } from 'react';
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
  const confirmation = useRef(null);

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
      const signature = memberIds.join(':');
      if (confirmation.current?.signature !== signature) {
        confirmation.current = { signature, key: crypto.randomUUID() };
      }
      const payload = { name: `Grupo de ${currentUser.name.split(' ')[0]}`, members: memberIds, idempotency_key: confirmation.current.key };
      const createdSextet = await roundService.createSextet(roundId, payload);
      setExistingSextet(createdSextet);
    } catch (err) {
      if (err.code === 'STUDENT_ALREADY_IN_SEXTET') {
        const existing = await roundService.getMySextet(roundId).catch(() => null);
        if (existing) { setExistingSextet(existing); return; }
      }
      const messages = { INTEGRITY_CONFLICT: 'Um dos integrantes já pertence a outro grupo ativo.', STUDENT_ALREADY_IN_SEXTET: 'Um dos integrantes já pertence a outro grupo ativo.', REGISTRATION_WINDOW_CLOSED: 'A janela de confirmação desta rodada foi encerrada.', IDEMPOTENCY_CONFLICT: 'Esta confirmação já foi usada com outra composição.', INVALID_SEXTET_COMPOSITION: 'O grupo deve ter de 3 a 6 alunos ativos.', DUPLICATE_MEMBER: 'Selecione alunos diferentes.' };
      setError(messages[err.code] || err.message || 'Falha ao confirmar o sexteto.');
    } finally { setIsSubmitting(false); }
  };

  return { round, existingSextet, isOccupiedGlobally, isLoading, isSubmitting, error, setError, submitSextet };
}
