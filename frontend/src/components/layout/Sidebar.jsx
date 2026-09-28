import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { House, UsersRound, ListOrdered, ClipboardCheck, CalendarDays, UserRoundPlus, ScrollText, LayoutDashboard } from 'lucide-react';
import { roundService } from '../../services/roundService';
import { useAuth } from '../../contexts/AuthContext';

const studentItems = [
  { path: '/aluno', icon: House, label: 'Início', exact: true },
  { path: '/aluno/sexteto', icon: UsersRound, label: 'Meu sexteto' },
  { path: '/aluno/preferencias', icon: ListOrdered, label: 'Preferências' },
  { path: '/aluno/resultado', icon: ClipboardCheck, label: 'Resultado' },
];
const adminItems = [
  { path: '/admin', icon: LayoutDashboard, label: 'Visão geral', exact: true },
  { path: '/admin/rodadas', icon: CalendarDays, label: 'Rodadas' },
  { path: '/admin/cadastros', icon: UserRoundPlus, label: 'Cadastros' },
  { path: '/admin/auditoria', icon: ScrollText, label: 'Auditoria' },
];

export function Sidebar() {
  const { user } = useAuth();
  const [roundId, setRoundId] = useState(null);
  useEffect(() => {
    if (user?.role === 'ADMIN') return;
    let active = true;
    roundService.getCurrentRound().then((round) => { if (active) setRoundId(round?.id || null); }).catch(() => {});
    return () => { active = false; };
  }, [user?.role]);
  const isAdmin = user?.role === 'ADMIN';
  const items = isAdmin ? adminItems : studentItems;
  const links = items.map((item) => {
    const Icon = item.icon;
    const path = !isAdmin && !item.exact && roundId ? `${item.path}/${roundId}` : item.path;
    return <NavLink key={item.path} to={path} end={item.exact} className={({ isActive }) => `app-nav-link${isActive ? ' is-active' : ''}`}><Icon size={18} strokeWidth={2} aria-hidden="true"/><span>{item.label}</span></NavLink>;
  });
  return <>
    <aside className="app-sidebar"><div className="app-sidebar-heading">{isAdmin ? 'ADMINISTRAÇÃO' : 'ÁREA DO ALUNO'}</div><nav aria-label="Navegação principal">{links}</nav><div className="app-sidebar-note"><span className="app-note-mark">✦</span><strong>Uma escolha mais justa.</strong><p>Cada etapa fica registrada para que o processo seja claro do início ao fim.</p></div></aside>
    <nav className="app-bottom-nav" aria-label="Navegação principal no celular">{links}</nav>
  </>;
}
