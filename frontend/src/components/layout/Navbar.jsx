import { useState, useEffect } from 'react';
import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { roundService } from '../../services/roundService';
import logo from '../../assets/ifsp.png';
import bgImage from '../../assets/images/campus-colored-gradient.jpg';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [roundName, setRoundName] = useState('Carregando...');
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    let isMounted = true;
    roundService.getCurrentRound()
      .then((round) => { if (isMounted) setRoundName(round ? round.name : 'Sem rodada disponível'); })
      .catch(() => { if (isMounted) setRoundName('Sistema IF-Arbitra'); });
    return () => { isMounted = false; };
  }, []);

  const handleLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try { await logout(); } finally { navigate('/auth', { replace: true }); setIsLoggingOut(false); }
  };

  const userName = user?.name || 'Usuário';
  const userIdentifier = user?.login || '---';
  const initials = userName.split(' ').map((name) => name[0]).join('').substring(0, 2).toUpperCase();

  return (
    <header className="bg-[#0A3D2A] text-white h-14 px-4 flex items-center justify-between shrink-0" style={{ backgroundImage: `url(${bgImage})`, backgroundSize: 'cover', backgroundPosition: 'center' }}>
      <div className="flex items-center gap-3"><img src={logo} alt="Logo IF-Arbitra" className="h-8" /><span className="font-bold text-[15px] tracking-wide">IF-Arbitra</span></div>
      <div className="text-[13px] font-medium text-green-50/90 hidden sm:block">{roundName}</div>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-white text-[#0A3D2A] flex items-center justify-center text-[12px] font-bold">{initials}</div>
        <div className="flex flex-col text-right hidden sm:flex"><span className="text-[13px] font-medium leading-none">{userName}</span><span className="text-[11px] text-green-200/80 mt-1">{userIdentifier}</span></div>
        <button type="button" onClick={handleLogout} disabled={isLoggingOut} className="p-2 rounded-md text-green-50 hover:bg-white/10 disabled:opacity-50" title="Sair" aria-label="Sair"><LogOut size={17} /></button>
      </div>
    </header>
  );
}
