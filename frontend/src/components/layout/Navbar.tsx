// frontend/src/components/layout/Navbar.tsx
import React from 'react';
import { useAuth } from '../../contexts/AuthContext'; // Importar hook

export function Navbar({ roundName = "Rodada 2026/2" }) { // roundName ainda pode ser prop, pois varia por rodada
  const { user } = useAuth(); // Pegar o usuário real

  // Fallbacks caso a tela renderize enquanto carrega
  const userName = user?.name || "Usuário";
  const userIdentifier = user?.login || "---";

  const initials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  return (
    <header className="bg-[#0A3D2A] text-white h-14 px-4 flex items-center justify-between shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="grid grid-cols-3 gap-[2px]">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="w-[6px] h-[6px] bg-white rounded-[1px] opacity-90"></div>
          ))}
        </div>
        <span className="font-bold text-[15px] tracking-wide">IF-Arbitra</span>
      </div>

      {/* Round Info */}
      <div className="text-[13px] font-medium text-green-50/90 hidden sm:block">
        {roundName}
      </div>


      {/* User Info */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-white text-[#0A3D2A] flex items-center justify-center text-[12px] font-bold">
          {initials}
        </div>
        <div className="flex flex-col text-right hidden sm:flex">
          <span className="text-[13px] font-medium leading-none">{userName}</span>
          <span className="text-[11px] text-green-200/80 mt-1">{userIdentifier}</span>
        </div>
      </div>
    </header>
  );
}