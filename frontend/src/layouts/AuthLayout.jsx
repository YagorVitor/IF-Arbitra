import { Outlet } from 'react-router-dom';
import IFArbitraLogo from '../components/IFArbitraLogo';

export default function AuthLayout() {
  return (
    <main className="min-h-screen bg-[#0A3D2A] flex flex-col items-center justify-center">
      
      <header className="flex flex-col items-center mb-8">
        <IFArbitraLogo/>

        <h1 className="text-white text-[22px] font-bold tracking-wide">
          IF-Arbitra
        </h1>

        <p className="text-green-100/80 text-[13px] font-medium">
          Instituto Federal
        </p>
      </header>

      <Outlet />

      <footer className="mt-8 text-green-100/60 text-xs font-medium">
        Instituto Federal Campus Araraquara
      </footer>

    </main>
  );
}