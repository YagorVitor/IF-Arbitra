import * as Dialog from '@radix-ui/react-dialog';
import { motion } from 'motion/react';
import { ArrowRight, CalendarClock, CalendarDays, Check, CircleHelp, ClipboardCheck, ListOrdered, Settings2, UsersRound, X } from 'lucide-react';
import { Link } from 'react-router-dom';

const steps = [
  { number: '01', icon: UsersRound, title: 'Formação dos trios', text: 'Cada trio confirma três integrantes durante o período de inscrições.' },
  { number: '02', icon: ListOrdered, title: 'Preferências', text: 'O líder ordena os servidores dentro do prazo informado na rodada.' },
  { number: '03', icon: Settings2, title: 'Processamento', text: 'Os dois primeiros trios compatíveis são reunidos para cada servidor, conforme a ordem das preferências.' },
  { number: '04', icon: ClipboardCheck, title: 'Resultado', text: 'A administração publica a alocação para consulta dos alunos.' },
];

function HowItWorksDialog() {
  return (
    <Dialog.Root>
      <Dialog.Trigger className="app-button secondary" type="button"><CircleHelp size={18} /> Como funciona</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="app-dialog-overlay" />
        <Dialog.Content className="app-dialog-content">
          <div className="app-dialog-top"><span className="app-kicker">PROCESSO DE ALOCAÇÃO</span><Dialog.Close aria-label="Fechar" className="app-dialog-close"><X size={20} /></Dialog.Close></div>
          <Dialog.Title className="app-dialog-title">Etapas da rodada</Dialog.Title>
          <Dialog.Description className="app-dialog-description">As datas de cada etapa são definidas pela administração e exibidas neste painel.</Dialog.Description>
          <div className="app-dialog-steps">{steps.map(({ number, icon: Icon, title, text }) => <div className="app-dialog-step" key={number}><span className="app-dialog-step-icon"><Icon size={20} /></span><div><small>ETAPA {number}</small><strong>{title}</strong><p>{text}</p></div></div>)}</div>
          <div className="app-dialog-note"><Check size={17} /> A prioridade é registrada na confirmação do trio.</div>
          <Dialog.Close className="app-button app-dialog-action">Fechar <ArrowRight size={16} /></Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export default function EmptyRoundState({ section = 'home' }) {
  if (section !== 'home') {
    const sections = { sexteto: ['Meu grupo', 'seu grupo'], preferencias: ['Preferências', 'as preferências'], resultado: ['Resultado', 'o resultado'] };
    const [title, subject] = sections[section] || ['Etapa', 'esta etapa'];
    return <div className="app-page"><div className="app-page-head"><div><p className="app-eyebrow">ÁREA DO ALUNO</p><h1 className="app-title">{title}</h1></div></div><section className="app-empty-compact app-card"><span className="app-empty-compact-icon"><CalendarClock size={27} /></span><span className="app-kicker">SEM RODADA ABERTA</span><h2>Ainda não há uma rodada para consultar {subject}.</h2><p>Quando a administração abrir o processo, esta área mostrará as informações e ações disponíveis.</p><Link className="app-button" to="/aluno">Voltar ao início <ArrowRight size={16} /></Link></section></div>;
  }

  return (
    <div className="app-page app-empty-page">
      <div className="app-page-head app-empty-heading"><div><p className="app-eyebrow">ÁREA DO ALUNO</p><h1 className="app-title">Visão geral</h1><p className="app-subtitle">Situação do processo de formação e alocação dos grupos.</p></div><span className="app-pill neutral">Sem rodada aberta</span></div>
      <motion.section className="app-empty-hero" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: .25 }}>
        <div className="app-empty-hero-copy"><div className="app-empty-hero-tag"><CalendarDays size={16} /> SITUAÇÃO DA RODADA</div><h2>Nenhuma rodada está aberta</h2><p>Não há inscrições, preferências ou resultados disponíveis no momento. As datas aparecem aqui quando a administração criar e abrir uma rodada.</p><div className="app-empty-hero-actions"><HowItWorksDialog /><a className="app-text-link" href="#etapas">Ver etapas <ArrowRight size={17} /></a></div></div>
        <div className="app-empty-hero-side" aria-label="Etapas ainda não iniciadas"><div className="app-round-visual"><div className="app-round-visual-top"><span className="app-round-visual-icon"><CalendarClock size={24} /></span><span className="app-round-visual-mini">IF-ARBITRA<br/>STATUS ATUAL</span></div><span className="app-kicker">PRÓXIMA AÇÃO</span><strong>Aguardar abertura</strong><p>O calendário da rodada será exibido após a publicação pela administração.</p><div className="app-round-status-row"><span>Inscrições</span><strong>Não iniciadas</strong></div><div className="app-round-status-row"><span>Preferências</span><strong>Não iniciadas</strong></div></div></div>
      </motion.section>
      <section id="etapas" className="app-empty-process"><div className="app-empty-section-heading"><div><p className="app-eyebrow">PROCESSO</p><h2>Etapas da rodada</h2></div><span>4 etapas</span></div><div className="app-empty-steps">{steps.map(({ number, icon: Icon, title, text }) => <article className="app-empty-step" key={number}><span className="app-empty-step-icon"><Icon size={21} /></span><div className="app-empty-step-content"><span className="app-empty-step-number">{number}</span><h3>{title}</h3><p>{text}</p></div><span className="app-empty-step-status">Aguardando</span></article>)}</div></section>
      <div className="app-empty-help"><CircleHelp size={19} /><p><strong>Dúvidas sobre a prioridade?</strong> A ordem é definida quando o trio é confirmado. Alterações nas preferências não mudam essa posição.</p><HowItWorksDialog /></div>
    </div>
  );
}
