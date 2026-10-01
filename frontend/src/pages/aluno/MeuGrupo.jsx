import { CheckCircle2, AlertCircle, Lock, Clock } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useGroupManager } from '../../hooks/useGroupManager';
import GroupForm from '../../components/ui/GroupForm';
import GroupReadOnly from '../../components/ui/GroupReadOnly';
import EmptyRoundState from '../../components/ui/EmptyRoundState';

export default function MeuGrupo() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { roundId } = useParams();
  const currentUser = { id: user?.id, name: user?.name || 'A carregar...', login: user?.login || '' };
  const { round, existingGroup, isOccupiedGlobally, isLoading, isSubmitting, error, setError, submitGroup } = useGroupManager(currentUser, roundId);

  if (isLoading) return <div className="app-card app-card-pad" role="status">Carregando informações...</div>;
  if (!round && !error) return <EmptyRoundState section="trio" />;
  if (!round && error) return <div className="app-error app-card" role="alert"><AlertCircle size={22}/><div><strong>Não foi possível consultar o grupo</strong><p>{error}</p><button type="button" className="app-button secondary" onClick={() => navigate('/aluno')}>Voltar ao início</button></div></div>;

  const trioMode = round?.formation_mode === 'TRIOS';
  const groupName = 'grupo';

  if (isOccupiedGlobally && !existingGroup) return (
    <div className="max-w-3xl mx-auto py-16 flex flex-col items-center text-center">
      <div className="w-16 h-16 bg-red-50 text-red-600 rounded-full flex items-center justify-center mb-4"><Lock size={32} /></div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Formulário bloqueado</h2>
      <p className="text-gray-600 mb-8 max-w-lg">Você já está registrado em um grupo ativo. Um aluno pode pertencer no máximo a um grupo ativo no sistema.</p>
      <button onClick={() => navigate('/aluno')} className="px-6 py-2 rounded-md font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors">Voltar ao painel</button>
    </div>
  );

  const isReadOnly = !!existingGroup;
  const canRegister = round?.formation_mode === 'GROUPS' && round?.registration_open === true;

  return (
    <div className="app-page">
      <div className="app-page-head">
        <div>
          <p className="app-eyebrow">{round?.name || 'Formação de grupos'}</p><h1 className="app-title">{isReadOnly ? `Meu ${groupName}` : `Formar ${groupName}`}</h1>
          <p className="app-subtitle">{isReadOnly ? `Prioridade registrada na rodada: #${String(existingGroup.priority_sequence || 0).padStart(2, '0')}` : 'Você é o capitão. Escolha cinco integrantes obrigatórios e um sétimo opcional.'}</p>
        </div>
        {isReadOnly && <div className="app-pill"><CheckCircle2 size={14}/>Confirmado</div>}
      </div>

      {error && <div role="alert" className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 flex items-center gap-3 text-sm"><AlertCircle className="shrink-0 text-red-600" size={20} /><span>{error}</span></div>}

      {isReadOnly ? <GroupReadOnly existingGroup={existingGroup} trioMode={trioMode} /> : canRegister ? (
        <GroupForm currentUser={currentUser} round={round} onSubmit={submitGroup} isSubmitting={isSubmitting} setError={setError} />
      ) : (
        <div className="max-w-3xl bg-amber-50 border border-amber-200 rounded-lg p-6 flex items-start gap-3 text-amber-900"><Clock className="shrink-0 mt-0.5" size={22} /><div><h2 className="font-bold">Confirmação indisponível</h2><p className="text-sm mt-1">{trioMode ? 'A confirmação ficará disponível durante o período de inscrições da rodada.' : 'Esta rodada está disponível para consulta. Aguarde a administração abrir uma nova rodada para confirmar seu grupo.'}</p></div></div>
      )}
    </div>
  );
}
