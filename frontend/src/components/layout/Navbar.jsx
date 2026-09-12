import { useAuth } from '../../contexts/AuthContext';
import IFArbitraLogo from '../IFArbitraLogo';

export function Navbar({ roundName = 'Rodada 2026/2' }) {
  const { user } = useAuth();

  const userName = user?.name || 'Usuário';
  const userIdentifier = user?.login || '---';

  const initials = userName
    .split(' ')
    .map((name) => name[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  return (
    <header className="bg-[#0A3D2A] text-white h-14 px-4 flex items-center justify-between shrink-0">

      <div className="flex items-center gap-3">
        <IFArbitraLogo/>

        <span className="font-bold text-[15px] tracking-wide">
          IF-Arbitra
        </span>
      </div>

      {/* Rodada */}
      <div className="text-[13px] font-medium text-green-50/90 hidden sm:block">
        {roundName}
      </div>

      {/* Usuário */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-white text-[#0A3D2A] flex items-center justify-center text-[12px] font-bold">
          {initials}
        </div>

        <div className="flex flex-col text-right hidden sm:flex">
          <span className="text-[13px] font-medium leading-none">
            {userName}
          </span>

          <span className="text-[11px] text-green-200/80 mt-1">
            {userIdentifier}
          </span>
        </div>
      </div>

    </header>
  );
}