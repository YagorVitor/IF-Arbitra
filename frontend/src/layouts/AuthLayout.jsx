import { Outlet } from 'react-router-dom';
import logo from '../assets/ifsp.png';
import bgImage from '../assets/images/campus-colored.jpg'


export default function AuthLayout() {
  return (
    <main 
    className="min-h-screen bg-[#0A3D2A] flex flex-col items-center justify-center"
    style={{ backgroundImage: `url(${bgImage})`, backgroundSize: 'cover', backgroundPosition: 'center' }}
    >
      
      <header className="flex flex-col items-center mb-8">
        <img src={logo} alt="IFSP Logo" className="w-24" />

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