import { CheckCircle2, AlertCircle, Lock, Clock } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useSextetManager } from '../../hooks/useSextetManager';
import SextetForm from '../../components/ui/SextetForm';
import SextetReadOnly from '../../components/ui/SextetReadOnly';

export default function MeuSexteto() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { roundId } = useParams();
  const currentUser = { id: user?.id, name: user?.name || 'A carregar...', login: user?.login || '' };
  const { round, existingSextet, isOccupiedGlobally, isLoading, isSubmitting, error, setError, submitSextet } = useSextetManager(currentUser, roundId);

  if (isLoading) return <div className="max-w-5xl mx-auto py-16 flex justify-center text-gray-500 font-medium">A carregar informações...</div>;

  if (isOccupiedGlobally && !existingSextet) return (
    <div className="max-w-3xl mx-auto py-16 flex flex-col items-center text-center">
      <div className="w-16 h-16 bg-red-50 text-red-600 rounded-full flex items-center justify-center mb-4"><Lock size={32} /></div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Formulário bloqueado</h2>
      <p className="text-gray-600 mb-8 max-w-lg">Você já está registrado em um sexteto ativo. Um aluno pode pertencer no máximo a um sexteto ativo no sistema.</p>
      <button onClick={() => navigate('/aluno')} className="px-6 py-2 rounded-md font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors">Voltar ao painel</button>
    </div>
  );

  const isReadOnly = !!existingSextet;
  const canRegister = round?.registration_open === true;

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">{isReadOnly ? 'O seu sexteto' : 'Formar sexteto'}</h1>
          <p className="text-gray-500 text-sm">{isReadOnly ? `Prioridade registrada na rodada: #${String(existingSextet.priority_sequence || 0).padStart(2, '0')}` : 'O seu sexteto deve ter exatamente 6 alunos, organizados em dois trios.'}</p>
        </div>
        {isReadOnly && <div className="self-start sm:self-auto bg-green-50 text-green-800 px-3 py-1.5 rounded-full text-xs font-bold border border-green-200 flex items-center gap-2"><CheckCircle2 size={16} className="text-green-600" /> Confirmado</div>}
      </div>

      {error && <div className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 flex items-center gap-3 text-sm"><AlertCircle className="shrink-0 text-red-600" size={20} /><span>{error}</span></div>}

      {isReadOnly ? <SextetReadOnly existingSextet={existingSextet} /> : canRegister ? (
        <SextetForm currentUser={currentUser} onSubmit={submitSextet} isSubmitting={isSubmitting} error={error} setError={setError} />
      ) : (
        <div className="max-w-3xl bg-amber-50 border border-amber-200 rounded-lg p-6 flex items-start gap-3 text-amber-900"><Clock className="shrink-0 mt-0.5" size={22} /><div><h2 className="font-bold">Confirmação indisponível</h2><p className="text-sm mt-1">A janela oficial de confirmação desta rodada não está aberta. O backend continuará sendo a autoridade sobre o prazo.</p></div></div>
      )}
    </div>
  );
}
