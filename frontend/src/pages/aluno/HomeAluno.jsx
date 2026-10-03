import { ArrowRight, Clock3, CircleCheck, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStudentDashboard } from '../../hooks/useStudentDashboard';
import EmptyRoundState from '../../components/ui/EmptyRoundState';
import CaptainSteps from '../../components/ui/CaptainSteps';
import { captainFlow } from '../../utils/captainFlow';

const messages = {
  group: { title: 'Comece pelo seu grupo', description: 'Você já é o capitão. Escolha mais cinco alunos e, se quiser, inclua um sétimo integrante. Depois de confirmar, você seguirá para as preferências.', action: 'Montar meu grupo', path: 'grupo', step: 1 },
  'registration-unavailable': { title: 'A confirmação de grupos está indisponível', description: 'Aguarde o período de inscrições definido pela administração. Se você perdeu o prazo, procure a organização.', step: 1 },
  preferences: { title: 'Grupo confirmado. Escolha os servidores.', description: 'Coloque os servidores na ordem que seu grupo prefere e envie a lista. Este é o último passo antes de aguardar o resultado.', action: 'Escolher e enviar preferências', path: 'preferencias', step: 2 },
  'preferences-unavailable': { title: 'Seu grupo está confirmado', description: 'Falta enviar as preferências. O envio está indisponível neste momento; acompanhe o período definido pela administração. Se o prazo já terminou, procure a organização.', step: 2 },
  waiting: { title: 'Tudo enviado. Aguarde o resultado.', description: 'Seu grupo e suas preferências estão registrados. Você não precisa enviar mais nada. O resultado aparecerá aqui quando a administração publicar a alocação.', step: 3 },
  result: { title: 'O resultado está disponível', description: 'Confira a situação do seu grupo e o servidor atribuído na página de resultado.', action: 'Ver resultado', path: 'resultado', step: 3 },
};

export default function HomeAluno() {
  const { loading, error, round, group, deadlineText } = useStudentDashboard();
  if (loading) return <div className="app-loading" role="status"><span className="app-loading-mark"/><div><strong>Preparando seu painel</strong><p>Buscando as informações da rodada...</p></div></div>;
  if (error) return <div className="app-error app-card" role="alert"><AlertCircle size={22}/><div><strong>Não foi possível carregar o painel</strong><p>{error}</p><button className="app-button secondary" onClick={() => window.location.reload()}>Tentar novamente</button></div></div>;
  if (!round) return <EmptyRoundState />;

  const flow = captainFlow(round, group);
  const message = messages[flow];
  const preferencesSent = group?.preference_version > 0 && group?.preferences?.length > 0;
  const unavailable = flow.endsWith('unavailable');

  return <div className="app-page app-student-home">
    <header className="app-page-head"><div><p className="app-eyebrow">Área do capitão</p><h1 className="app-title">{round.name}</h1><p className="app-subtitle">Monte o grupo, envie as preferências e acompanhe o resultado.</p></div></header>
    <CaptainSteps current={message.step} groupConfirmed={!!group} preferencesSent={preferencesSent}/>
    <section className={`app-card app-card-pad app-captain-next ${flow === 'waiting' ? 'is-sent' : ''}`}>
      <span className="app-icon-bubble">{unavailable ? <AlertCircle size={24}/> : flow === 'waiting' || flow === 'result' ? <CircleCheck size={24}/> : <ArrowRight size={24}/>}</span>
      <div className="app-captain-next-copy"><p className="app-label">{flow === 'waiting' ? 'Envio concluído' : flow === 'result' ? 'Resultado publicado' : `Passo ${message.step} de 3`}</p><h2>{message.title}</h2><p>{message.description}</p>
        {message.action && <Link className="app-button" to={`/aluno/${message.path}/${round.id}`}>{message.action}<ArrowRight size={17}/></Link>}
        {flow === 'waiting' && round.preferences_open && <p className="app-muted text-sm">Você pode revisar a lista enquanto o prazo estiver aberto.</p>}
      </div>
    </section>
    <div className="app-captain-summary">
      <span className="app-stage-time"><Clock3 size={17}/>{deadlineText}</span>
      {group && <span>{group.member_count} integrantes · prioridade #{String(group.priority_sequence || 0).padStart(2, '0')}</span>}
    </div>
    {group && <nav className="app-captain-review" aria-label="Revisar sua participação"><Link className="app-button secondary" to={`/aluno/grupo/${round.id}`}>Consultar meu grupo</Link>{preferencesSent && <Link className="app-button secondary" to={`/aluno/preferencias/${round.id}`}>{round.preferences_open ? 'Revisar preferências' : 'Consultar preferências enviadas'}</Link>}</nav>}
    {flow !== 'waiting' && flow !== 'result' && <div className="app-notice"><strong>Como funciona a prioridade?</strong>O horário da confirmação do grupo define sua posição de desempate. Alterar as preferências não muda esse horário.</div>}
  </div>;
}
