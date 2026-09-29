import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, UsersRound, GraduationCap, UserRoundCheck, ListChecks, AlertTriangle, CalendarDays } from 'lucide-react';
import { adminService } from '../../services/adminService';

const statuses = ['DRAFT', 'OPEN', 'PROCESSED', 'PUBLISHED', 'ARCHIVED'];
const labels = ['Rascunho', 'Aberta', 'Processada', 'Publicada', 'Arquivada'];

export default function AdminOverview() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    Promise.all([adminService.rounds(), adminService.students(), adminService.staff()])
      .then(([rounds, students, staff]) => { if (active) setData({ rounds, students, staff }); })
      .catch((err) => { if (active) setError(err.message || 'Não foi possível carregar a visão geral.'); });
    return () => { active = false; };
  }, []);
  if (error) return <div className="app-card app-card-pad" role="alert">{error}</div>;
  if (!data) return <div className="app-card app-card-pad" role="status">Carregando visão geral...</div>;

  const round = data.rounds.find((item) => item.status === 'OPEN') || data.rounds[0];
  const activeStaff = data.staff.filter((item) => item.active !== false).length;
  const trioMode = round?.formation_mode === 'TRIOS';
  const metrics = [
    { label: trioMode ? 'Trios confirmados' : 'Grupos registrados', value: round?.registered ?? 0, icon: UsersRound },
    { label: 'Alunos cadastrados', value: data.students.length, icon: GraduationCap },
    { label: trioMode ? 'Vagas para trios' : 'Servidores elegíveis', value: round?.capacity ?? activeStaff, icon: UserRoundCheck },
    { label: 'Listas enviadas', value: round?.with_preferences ?? 0, icon: ListChecks },
    { label: trioMode ? 'Trios pendentes' : 'Sem capacidade', value: trioMode ? (round?.pending ?? 0) : (round?.shortfall ?? 0), icon: AlertTriangle, danger: (trioMode ? round?.pending : round?.shortfall) > 0 },
  ];
  const statusIndex = statuses.indexOf(round?.status);

  return <div className="app-page">
    <div className="app-page-head"><div><p className="app-eyebrow">Administração · visão geral</p><h1 className="app-title">Acompanhe a alocação</h1><p className="app-subtitle">Indicadores da rodada e acesso às ações do processo.</p></div><Link className="app-button" to="/admin/rodadas">Gerenciar rodadas <ArrowRight size={15}/></Link></div>
    {!round ? <div className="app-card app-card-pad"><div className="app-section-head"><div><h2>Nenhuma rodada criada</h2><p>Cadastre servidores, defina os prazos e crie o primeiro rascunho.</p></div><CalendarDays size={24}/></div><Link to="/admin/rodadas" className="app-button">Criar rodada <ArrowRight size={15}/></Link></div> : <>
      <section className="app-card app-card-pad"><div className="app-section-head"><div><p className="app-label">Rodada em destaque</p><h2 className="app-title" style={{fontSize:25,marginTop:6}}>{round.name}</h2><p>{round.registered} {trioMode ? 'trios' : 'grupos registrados'} confirmados · {round.with_preferences} listas de preferências</p></div><span className={`app-pill ${round.status === 'OPEN' ? '' : 'neutral'}`}>{labels[statusIndex] || round.status}</span></div><div className="app-timeline" aria-label="Progresso da rodada">{labels.map((label,index) => <div key={label} className={`app-timeline-item ${index === statusIndex ? 'active' : ''}`}><span className="app-timeline-dot"/>{label}</div>)}</div></section>
      <div className="app-grid-3 app-admin-metrics">{metrics.map(({label,value,icon:Icon,danger}) => <div className={`app-stat ${danger ? 'danger' : ''}`} key={label}><div className="app-stat-icon"><Icon size={19}/></div><div><strong>{value}</strong><span>{label}</span></div></div>)}</div>
      <div className="app-grid-2"><section className="app-card app-card-pad"><div className="app-section-head"><div><h2>Próxima ação</h2><p>O servidor valida os prazos e as transições.</p></div></div><p className="text-sm app-muted mb-5">{round.status === 'DRAFT' ? 'Revise os prazos e servidores antes de abrir a rodada.' : round.status === 'OPEN' ? round.can_process ? 'A janela de preferências terminou. Confira os grupos e processe a alocação.' : 'Acompanhe as confirmações e as listas de preferências.' : round.status === 'PROCESSED' ? 'Revise os resultados antes de publicá-los para os alunos.' : 'Consulte os resultados e os registros da rodada.'}</p><Link className="app-button secondary" to="/admin/rodadas">Abrir rodadas <ArrowRight size={15}/></Link></section><section className="app-card app-card-pad"><div className="app-section-head"><div><h2>Transparência do processo</h2><p>Eventos e alterações ficam registrados.</p></div></div><p className="text-sm app-muted mb-5">Consulte a trilha de auditoria para acompanhar confirmação, preferências, processamento e publicação.</p><Link className="app-button secondary" to="/admin/auditoria">Ver auditoria <ArrowRight size={15}/></Link></section></div>
    </>}
  </div>;
}
