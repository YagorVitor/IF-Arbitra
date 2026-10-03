import { useState, useEffect, useRef } from 'react';
import { roundService } from '../services/roundService';
import { studentService } from '../services/studentService';

export function useGroupManager(currentUser, initialRoundId) {
  const [roundId, setRoundId] = useState(initialRoundId || null);
  const [round, setRound] = useState(null);
  const [existingGroup, setExistingGroup] = useState(null);
  const [isOccupiedGlobally, setIsOccupiedGlobally] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const confirmation = useRef(null);

  useEffect(() => {
    async function resolveRound() {
      if (initialRoundId) { setRoundId(initialRoundId); return; }
      try {
        const openRound = await roundService.getCurrentRound();
        if (openRound) { setRound(openRound); setRoundId(openRound.id); }
        else { setRound(null); setIsLoading(false); }
      } catch (err) { setError(err.message || 'Erro ao carregar rodadas.'); setIsLoading(false); }
    }
    resolveRound();
  }, [initialRoundId]);

  useEffect(() => {
    async function fetchMyGroup() {
      if (!roundId || !currentUser?.login) return;
      setIsLoading(true); setError('');
      try {
        const [roundData, groupData] = await Promise.all([
          roundService.getById(roundId),
          roundService.getMyGroup(roundId),
        ]);
        setRound(roundData);
        if (groupData?.id) setExistingGroup(groupData);
        else {
          setExistingGroup(null);
          const students = await studentService.search(currentUser.login);
          const me = students.find((s) => s.login.toLowerCase() === currentUser.login.toLowerCase());
          setIsOccupiedGlobally(Boolean(me?.occupied));
        }
      } catch (err) { setError(err.message || 'Erro ao verificar grupo existente.'); }
      finally { setIsLoading(false); }
    }
    fetchMyGroup();
  }, [roundId, currentUser?.login]);

  const submitGroup = async (memberIds) => {
    if (round?.formation_mode !== 'GROUPS' || ![6, 7].includes(memberIds.length)) { setError('Confirme seis integrantes obrigatórios e, se desejar, um sétimo.'); return; }
    if (!round?.registration_open) { setError('A janela de confirmação desta rodada está encerrada.'); return; }
    setIsSubmitting(true); setError('');
    try {
      const signature = memberIds.join(':');
      if (confirmation.current?.signature !== signature) {
        confirmation.current = { signature, key: crypto.randomUUID() };
      }
      const payload = { name: `Grupo de ${currentUser.name.split(' ')[0]}`, members: memberIds, idempotency_key: confirmation.current.key };
      const createdGroup = await roundService.createGroup(roundId, payload);
      setExistingGroup(createdGroup);
      return createdGroup;
    } catch (err) {
      if (err.code === 'STUDENT_ALREADY_IN_SEXTET') {
        const existing = await roundService.getMyGroup(roundId).catch(() => null);
        if (existing) { setExistingGroup(existing); return existing; }
      }
      const messages = { CAPTAIN_AS_MEMBER: "Outro capitão não pode ser incluído no seu grupo.", CAPTAIN_REQUIRED: "Somente capitães cadastrados podem confirmar grupos.", INTEGRITY_CONFLICT: 'Um dos integrantes já pertence a outro grupo ativo.', STUDENT_ALREADY_IN_SEXTET: 'Um dos integrantes já pertence a outro grupo ativo.', REGISTRATION_WINDOW_CLOSED: 'A janela de confirmação desta rodada foi encerrada.', IDEMPOTENCY_CONFLICT: 'Esta confirmação já foi usada com outra composição.', INVALID_SEXTET_COMPOSITION: 'Selecione apenas alunos ativos.', INVALID_GROUP_COMPOSITION: 'Confirme seis integrantes, incluindo o capitão, e um sétimo opcional.', DUPLICATE_MEMBER: 'Selecione alunos diferentes.' };
      setError(messages[err.code] || err.message || 'Falha ao confirmar o grupo.');
    } finally { setIsSubmitting(false); }
  };

  return { round, existingGroup, isOccupiedGlobally, isLoading, isSubmitting, error, setError, submitGroup };
}
