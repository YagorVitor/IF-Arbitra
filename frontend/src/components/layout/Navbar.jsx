import { useState, useEffect } from 'react';
import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { roundService } from '../../services/roundService';
import logo from '../../assets/ifsp.png';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [roundName, setRoundName] = useState('IF-Arbitra');
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    let active = true;
    roundService.getCurrentRound()
      .then((round) => { if (active) setRoundName(round?.name || 'Sem rodada disponível'); })
      .catch(() => { if (active) setRoundName('IF-Arbitra'); });
    return () => { active = false; };
  }, []);

  const handleLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try { await logout(); } finally { navigate('/auth', { replace: true }); setIsLoggingOut(false); }
  };
  const userName = user?.name || 'Usuário';
  const initials = userName.split(' ').slice(0, 2).map((name) => name[0]).join('').toUpperCase();

  return (
    <header className="app-topbar">
      <a className="skip-link" href="#conteudo">Ir para o conteúdo</a>
      <div className="app-brand" aria-label="IF-Arbitra, Instituto Federal">
        <img src={logo} alt="" /><div><strong>IF-Arbitra</strong><span>Instituto Federal</span></div>
      </div>
      <div className="app-topbar-center"><span className="app-topbar-eyebrow">Sistema de alocação de grupos</span><span>{roundName}</span></div>
      <div className="app-account">
        <span className="app-avatar" aria-hidden="true">{initials}</span>
        <div className="app-account-name"><strong>{userName}</strong><span>{user?.role === 'ADMIN' ? 'Administrador' : 'Aluno'}</span></div>
        <button type="button" onClick={handleLogout} disabled={isLoggingOut} className="app-logout" title="Sair" aria-label="Sair"><LogOut size={18} /></button>
      </div>
    </header>
  );
}
