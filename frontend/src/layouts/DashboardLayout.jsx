import { Outlet } from 'react-router-dom';
import { MotionConfig } from 'motion/react';
import { Toaster } from 'sonner';
import { Navbar } from '../components/layout/Navbar';
import { Sidebar } from '../components/layout/Sidebar';
import '../styles/dashboard.css';
import '../styles/dashboard-refresh.css';

export default function DashboardLayout() {
  return (
    <MotionConfig reducedMotion="user"><div className="app-shell">
      <Navbar />
      <div className="app-frame">
        <Sidebar />
        <main id="conteudo" className="app-main"><Outlet /></main>
      </div>
      <footer className="app-footer"><strong>IF-Arbitra</strong><span>Sistema de alocação de grupos</span><span>Instituto Federal</span></footer>
      <Toaster position="bottom-right" richColors closeButton />
    </div></MotionConfig>
  );
}
