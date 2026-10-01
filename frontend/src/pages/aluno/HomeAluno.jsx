import { ArrowRight, UsersRound, ListOrdered, Clock3, CircleCheck, AlertCircle, CalendarDays } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStudentDashboard } from '../../hooks/useStudentDashboard';
import EmptyRoundState from '../../components/ui/EmptyRoundState';

const stageTitles = ['Formação do grupo', 'Preferências de servidores', 'Processamento da alocação', 'Resultado da rodada'];
const statusLabels = { DRAFT: 'Aguardando abertura', OPEN: 'Em andamento', PROCESSED: 'Aguardando publicação', PUBLISHED: 'Publicado', ARCHIVED: 'Arquivado' };

export default function HomeAluno() {
  const { loading, error, round, group, currentStage, deadlineText } = useStudentDashboard();
  if (loading) return <div className="app-loading" role="status"><span className="app-loading-mark"/><div><strong>Preparando seu painel</strong><p>Buscando as informações da rodada...</p></div></div>;
  if (error) return <div className="app-error app-card" role="alert"><AlertCircle size={22}/><div><strong>Não foi possível carregar o painel</strong><p>{error}</p><button className="app-button secondary" onClick={() => window.location.reload()}>Tentar novamente</button></div></div>;
  if (!round) return <EmptyRoundState />;

  const totalStaff = round.staff?.length || 0;
  const orderedCount = group?.preferences?.length || 0;
  const suffix = round.id ? `/${round.id}` : '';

  const canRegister = round.formation_mode === 'GROUPS' && round.registration_open && !group;
  const canEditPreferences = round.preferences_open && !!group;
  const status = statusLabels[round.status] || 'Em andamento';
  const groupName = 'grupo';
  const stages = ['Grupo', 'Preferências', 'Processamento', 'Resultado'];

  return <div className="app-page app-student-home">
    <section className="app-round-hero"><div className="app-round-hero-content"><p className="app-eyebrow">RODADA ATUAL</p><div className="app-round-hero-title"><h1>{round.name}</h1><span className={`app-pill ${round.status === 'OPEN' ? '' : 'neutral'}`}>{status}</span></div><p>{'Grupos com seis integrantes obrigatórios e um sétimo opcional. O capitão confirma a composição e ordena os servidores.'}</p><div className="app-round-hero-date"><CalendarDays size={18}/>{deadlineText}</div></div><div className="app-round-hero-decoration" aria-hidden="true"><span>IF</span><span>ARBITRA</span></div></section>
    <div className="app-steps" aria-label="Etapas da rodada">{stages.map((stage, index) => { const number = index + 1; const done = number < currentStage && (number === 1 ? !!group : number === 2 ? totalStaff > 0 && orderedCount === totalStaff : true); const active = number === currentStage; return <div className={`app-step ${done ? 'done' : ''} ${active ? 'active' : ''}`} key={stage} aria-current={active ? 'step' : undefined}><span className="app-step-number">{done ? '✓' : number}</span><strong>{stage}</strong><small>{done ? 'Concluído' : number < currentStage ? (number === 2 ? 'Não enviadas' : 'Não confirmado') : active ? 'Etapa atual' : 'Aguardando'}</small></div>; })}</div>
    <div className="app-stage"><div><p className="app-label">ETAPA ATUAL · {currentStage} DE 4</p><h2>{currentStage === 1 ? `Formação do ${groupName}` : stageTitles[currentStage - 1]}</h2></div><div className="app-stage-time"><Clock3 size={17}/>{deadlineText}</div></div>
    <div className="app-grid-2">
      <section className="app-card app-card-pad app-feature"><div><div className="app-section-head"><div><div className="app-icon-bubble mb-3"><UsersRound size={21}/></div><h2>Seu {groupName}</h2><p>{'Um grupo de 6 ou 7 integrantes, incluindo o capitão.'}</p></div><span className={`app-pill ${group ? '' : 'warning'}`}>{group ? 'Confirmado' : 'Pendente'}</span></div>{group ? <div className="app-feature-info"><span className="app-label">Sua prioridade</span><strong>#{String(group.priority_sequence || 0).padStart(2, '0')}</strong><p><CircleCheck size={14} className="inline mr-1"/>{group.member_count} alunos confirmados</p></div> : <p className="app-muted text-sm my-5">{canRegister ? 'As inscrições estão abertas. Monte seu grupo e confirme sua participação.' : `A confirmação do ${groupName} estará disponível no período de inscrições.`}</p>}</div><Link className="app-button secondary" to={`/aluno/grupo${suffix}`}>{group ? `Ver meu ${groupName}` : canRegister ? `Formar ${groupName}` : 'Ver informações'}<ArrowRight size={16}/></Link></section>
      <section className="app-card app-card-pad app-feature"><div><div className="app-section-head"><div><div className="app-icon-bubble mb-3"><ListOrdered size={21}/></div><h2>Preferências</h2><p>Ordem dos servidores para o seu grupo.</p></div><span className="app-pill neutral">Versão {group?.preference_version ?? 0}</span></div><div className="app-feature-info"><span className="app-label">Lista ordenada</span><strong>{orderedCount} de {totalStaff}</strong><div className="app-progress" role="progressbar" aria-valuenow={orderedCount} aria-valuemin="0" aria-valuemax={totalStaff || 1}><span style={{ width: totalStaff ? `${orderedCount / totalStaff * 100}%` : '0%' }} /></div></div></div>{canEditPreferences ? <Link className="app-button secondary" to={`/aluno/preferencias${suffix}`}>Revisar preferências<ArrowRight size={16}/></Link> : <span className="app-button secondary app-button-inactive" aria-disabled="true">Preferências indisponíveis</span>}</section>
    </div>
    <div className="app-notice"><strong>Como funciona a prioridade?</strong>Ela é definida no momento em que o {groupName} é confirmado. Editar as preferências depois não muda essa posição.</div>
  </div>;
}
