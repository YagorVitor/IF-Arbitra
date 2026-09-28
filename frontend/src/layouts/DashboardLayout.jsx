import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/layout/Navbar';
import { Sidebar } from '../components/layout/Sidebar';
import '../styles/dashboard.css';

export default function DashboardLayout() {
  return (
    <div className="app-shell">
      <Navbar />
      <div className="app-frame">
        <Sidebar />
        <main id="conteudo" className="app-main"><Outlet /></main>
      </div>
      <footer className="app-footer"><strong>IF-Arbitra</strong><span>Equidade, transparência e oportunidades.</span><span>Instituto Federal</span></footer>
    </div>
  );
}
