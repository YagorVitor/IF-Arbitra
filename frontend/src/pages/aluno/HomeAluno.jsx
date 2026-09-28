import { ArrowRight, UsersRound, ListOrdered, Clock3, CircleCheck, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStudentDashboard } from '../../hooks/useStudentDashboard';

const stages = ['Sexteto', 'Preferências', 'Processamento', 'Resultado'];
const stageTitles = ['Formação do sexteto', 'Preferências de servidores', 'Processamento da alocação', 'Resultado da rodada'];

export default function HomeAluno() {
  const { loading, error, round, sextet, currentStage, deadlineText } = useStudentDashboard();
  if (loading) return <div className="app-card app-card-pad" role="status">Carregando painel do aluno...</div>;
  if (error) return <div className="app-card app-card-pad" role="alert"><AlertCircle size={20} className="text-red-600 inline mr-2"/>{error}</div>;

  const totalStaff = round?.staff?.length || 0;
  const orderedCount = sextet?.preferences?.length || 0;
  const suffix = round?.id ? `/${round.id}` : '';
  const canRegister = round?.registration_open && !sextet;
  const canEditPreferences = round?.preferences_open && !!sextet;
  const status = round?.status === 'OPEN' ? 'Em andamento' : round?.status === 'PUBLISHED' ? 'Publicado' : round?.status === 'ARCHIVED' ? 'Arquivado' : 'Em processamento';

  return <div className="app-page">
    <div className="app-page-head"><div><p className="app-eyebrow">Sua jornada na rodada</p><h1 className="app-title">{round?.name || 'Processo de alocação'}</h1><p className="app-subtitle">Formação dos sextetos e escolha dos servidores</p></div><span className={`app-pill ${round?.status === 'OPEN' ? '' : 'neutral'}`}>{status}</span></div>
    <div className="app-steps" aria-label="Etapas da rodada">{stages.map((stage, index) => { const number = index + 1; const done = number < currentStage; const active = number === currentStage; return <div className={`app-step ${done ? 'done' : ''} ${active ? 'active' : ''}`} key={stage} aria-current={active ? 'step' : undefined}><span className="app-step-number">{done ? '✓' : number}</span><strong>{stage}</strong><small>{done ? 'Concluído' : active ? 'Etapa atual' : 'Aguardando'}</small></div>; })}</div>
    <div className="app-stage"><div><p className="app-label">Etapa atual · {currentStage} de 4</p><h2>{stageTitles[currentStage - 1]}</h2></div><div className="app-stage-time"><Clock3 size={16} className="inline mr-1"/>{deadlineText}</div></div>
    <div className="app-grid-2">
      <section className="app-card app-card-pad app-feature"><div><div className="app-section-head"><div><div className="app-icon-bubble mb-3"><UsersRound size={21}/></div><h2>Seu sexteto</h2><p>O grupo que participará desta rodada.</p></div><span className={`app-pill ${sextet ? '' : 'warning'}`}>{sextet ? 'Confirmado' : 'Pendente'}</span></div>{sextet ? <div className="app-feature-info"><span className="app-label">Sua prioridade</span><strong>#{String(sextet.priority_sequence || 0).padStart(2, '0')}</strong><p><CircleCheck size={14} className="inline mr-1"/>{sextet.member_count} alunos confirmados</p></div> : <p className="app-muted text-sm my-5">Você ainda não faz parte de um sexteto confirmado nesta rodada.</p>}</div><Link className="app-button secondary" to={`/aluno/sexteto${suffix}`}>{sextet ? 'Ver meu sexteto' : canRegister ? 'Formar sexteto' : 'Consultar sexteto'}<ArrowRight size={15}/></Link></section>
      <section className="app-card app-card-pad app-feature"><div><div className="app-section-head"><div><div className="app-icon-bubble mb-3"><ListOrdered size={21}/></div><h2>Preferências</h2><p>Ordem dos servidores para o seu grupo.</p></div><span className="app-pill neutral">Versão {sextet?.preference_version ?? 0}</span></div><div className="app-feature-info"><span className="app-label">Lista ordenada</span><strong>{orderedCount} de {totalStaff}</strong><div className="app-progress" role="progressbar" aria-valuenow={orderedCount} aria-valuemin="0" aria-valuemax={totalStaff || 1}><span style={{ width: totalStaff ? `${orderedCount / totalStaff * 100}%` : '0%' }} /></div></div></div>{canEditPreferences ? <Link className="app-button secondary" to={`/aluno/preferencias${suffix}`}>Revisar preferências<ArrowRight size={15}/></Link> : <span className="app-button secondary opacity-50" aria-disabled="true">Preferências indisponíveis</span>}</section>
    </div>
    <div className="app-notice"><strong>Como funciona a prioridade?</strong>Ela é definida no momento em que o sexteto é confirmado. Editar as preferências depois não muda essa posição.</div>
  </div>;
}
