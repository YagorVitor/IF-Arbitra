import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Users, ListOrdered, FileCheck2 } from 'lucide-react';
import { roundService } from '../../services/roundService';

const baseMenuItems = [
  { path: '/aluno', icon: Home, label: 'Início', exact: true },
  { path: '/aluno/sexteto', icon: Users, label: 'Meu sexteto', exact: false },
  { path: '/aluno/preferencias', icon: ListOrdered, label: 'Preferências', exact: false },
  { path: '/aluno/resultado', icon: FileCheck2, label: 'Resultado', exact: false },
];

export function Sidebar() {
  const [roundId, setRoundId] = useState(null);

  // Consulta a rodada e acopla o UUID nas rotas laterais dinamicamente
  useEffect(() => {
    let isMounted = true;
    roundService.getActiveRound()
      .then(round => {
        if (isMounted && round) setRoundId(round.id);
      })
      .catch(console.error);
    return () => { isMounted = false; };
  }, []);

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col shrink-0 min-h-[calc(100vh-3.5rem)]">
      <nav className="p-3 flex flex-col gap-1">
        {baseMenuItems.map((item) => {
          const Icon = item.icon;
          const targetPath = (item.exact || !roundId) ? item.path : `${item.path}/${roundId}`;

          return (
            <NavLink
              key={item.label}
              to={targetPath}
              end={item.exact}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-[13px] font-medium transition-colors ${
                  isActive ? 'bg-gray-200 text-gray-900' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`
              }
            >
              <Icon size={16} strokeWidth={2.5} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}