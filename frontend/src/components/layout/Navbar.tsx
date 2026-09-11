// frontend/src/components/layout/Navbar.tsx
import React from 'react';

interface NavbarProps {
  roundName?: string;
  userName?: string;
  userIdentifier?: string;
}

export function Navbar({ 
  roundName = "Rodada 2026/2", 
  userName = "Yagor Santos", 
  userIdentifier = "AQ3021416" 
}: NavbarProps) {
  // Extrai iniciais (ex: "Yagor Santos" -> "YS")
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