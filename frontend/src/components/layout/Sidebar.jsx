import { NavLink } from 'react-router-dom';
import { Home, Users, ListOrdered, FileCheck2 } from 'lucide-react';

const menuItems = [
  { path: '/aluno', icon: Home, label: 'Início' },
  { path: '/aluno/sexteto', icon: Users, label: 'Meu sexteto' },
  { path: '/aluno/preferencias', icon: ListOrdered, label: 'Preferências' },
  { path: '/aluno/resultado', icon: FileCheck2, label: 'Resultado' },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col shrink-0 min-h-[calc(100vh-3.5rem)]">
      <nav className="p-3 flex flex-col gap-1">
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-[13px] font-medium transition-colors ${
                  isActive
                    ? 'bg-gray-200 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
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