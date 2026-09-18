import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useStudentDashboard } from '../../hooks/useStudentDashboard';

export default function HomeAluno() {
  const navigate = useNavigate();
  const { loading, error, round, sextet, currentStage, deadlineText } = useStudentDashboard();

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Carregando painel do aluno...</div>;
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6 bg-red-50 border border-red-200 text-red-800 rounded-lg flex items-center gap-3">
        <AlertCircle className="text-red-600" size={20} />
        <span>{error}</span>
      </div>
    );
  }

  const totalStaff = round?.staff?.length || 0;
  const orderedCount = sextet?.preferences?.length || 0;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-10">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">
            {round?.name || 'Processo de alocação'}
          </h1>
          <p className="text-gray-500 text-sm">Formação dos sextetos e escolha dos servidores</p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1 bg-green-50 text-green-700 rounded-full text-xs font-semibold border border-green-100">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          {round?.status === 'OPEN' ? 'Em andamento' : round?.status}
        </div>
      </div>

      {/* Stepper de Etapas */}
      <div className="mb-12">
        <div className="flex items-center justify-between relative">
          <div className="absolute top-4 left-0 w-full h-[2px] bg-gray-200 -z-10" />
          <div 
            className="absolute top-4 left-0 h-[2px] bg-green-600 -z-10 transition-all duration-300" 
            style={{ width: `${((currentStage - 1) / 3) * 100}%` }}
          />

          {/* Etapa 1: Sexteto */}
          <StepItem 
            stepNumber="01" 
            label="Sexteto" 
            statusText={sextet ? 'Concluído' : 'Em andamento'} 
            isActive={currentStage === 1}
            isCompleted={!!sextet}
          />

          {/* Etapa 2: Preferências */}
          <StepItem 
            stepNumber="02" 
            label="Preferências" 
            statusText={currentStage > 2 ? 'Concluído' : currentStage === 2 ? 'Em andamento' : 'Bloqueado'} 
            isActive={currentStage === 2}
            isCompleted={currentStage > 2}
          />

          {/* Etapa 3: Processamento */}
          <StepItem 
            stepNumber="03" 
            label="Processamento" 
            statusText={currentStage > 3 ? 'Concluído' : currentStage === 3 ? 'Em andamento' : 'Bloqueado'} 
            isActive={currentStage === 3}
            isCompleted={currentStage > 3}
          />

          {/* Etapa 4: Resultado */}
          <StepItem 
            stepNumber="04" 
            label="Resultado" 
            statusText={currentStage === 4 ? 'Publicado' : 'Bloqueado'} 
            isActive={currentStage === 4}
            isCompleted={currentStage === 4}
          />
        </div>
      </div>

      {/* Banner de Etapa Atual */}
      <div className="mb-8 border-b border-gray-200 pb-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Etapa Atual</p>
          <h2 className="text-xl font-bold text-gray-900">
            {currentStage === 1 && 'Formação de Sextetos'}
            {currentStage === 2 && 'Preferências de Servidores'}
            {currentStage === 3 && 'Processamento de Alocação'}
            {currentStage === 4 && 'Resultado Final'}
          </h2>
        </div>

        <div className="text-right">
          <div className="text-xs text-gray-500">{deadlineText}</div>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Resumo do Sexteto */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-gray-900">Sexteto</h3>
              {sextet ? (
                <span className="flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-md">
                  <CheckCircle2 size={14} className="text-green-600" /> Confirmado
                </span>
              ) : (
                <span className="text-xs font-medium text-amber-700 bg-amber-50 px-2 py-1 rounded-md">
                  Pendente
                </span>
              )}
            </div>

            {sextet ? (
              <>
                <p className="text-xs text-gray-500 mb-1">Sua prioridade</p>
                <p className="text-lg font-bold text-gray-900">
                  #{String(sextet.priority_sequence || 0).padStart(2, '0')}
                </p>
              </>
            ) : (
              <p className="text-xs text-gray-500">Você ainda não faz parte de um sexteto confirmado nesta rodada.</p>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-gray-100">
            <button
              onClick={() => navigate('/aluno/meu-sexteto')}
              className="w-full py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              {sextet ? 'Ver meu sexteto' : 'Formar sexteto'}
            </button>
          </div>
        </div>

        {/* Resumo de Preferências */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-gray-900">Preferências</h3>
              <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-md">
                Versão {sextet?.preference_version ?? 0}
              </span>
            </div>

            <p className="text-xs text-gray-500 mb-1">
              {orderedCount} de {totalStaff} ordenadas
            </p>
            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mt-2">
              <div 
                className="h-full bg-green-600 rounded-full transition-all duration-300"
                style={{ width: totalStaff > 0 ? `${(orderedCount / totalStaff) * 100}%` : '0%' }}
              />
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-100">
            <button
              disabled={!sextet || !round?.preferences_open}
              onClick={() => navigate('/aluno/preferencias')}
              className="w-full py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Revisar preferências
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Subcomponente de item da timeline
function StepItem({ stepNumber, label, statusText, isActive, isCompleted }) {
  let circleStyle = 'bg-gray-50 text-gray-400 border-gray-300';
  let labelStyle = 'text-gray-500 font-medium';

  if (isActive) {
    circleStyle = 'bg-[#0A3D2A] text-white border-[#0A3D2A] shadow-[0_0_0_3px_rgba(10,61,42,0.1)]';
    labelStyle = 'text-gray-900 font-bold';
  } else if (isCompleted) {
    circleStyle = 'bg-green-100 text-green-600 border-green-600';
    labelStyle = 'text-green-700 font-bold';
  }

  return (
    <div className="flex flex-col items-center bg-white px-2">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs border-2 mb-2 ${circleStyle}`}>
        {stepNumber}
      </div>
      <span className={`text-xs mb-0.5 ${labelStyle}`}>{label}</span>
      <span className="text-[10px] text-gray-400">{statusText}</span>
    </div>
  );
}