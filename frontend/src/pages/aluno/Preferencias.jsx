import { useParams } from 'react-router-dom';
import { ListOrdered, Save } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { usePreferencesManager } from '../../hooks/usePreferencesManager';
import Alert from '../../components/ui/Alert';
import PreferenceListItem from '../../components/ui/PreferenceListItem';

export default function Preferencias() {
  const { roundId } = useParams();
  const { user } = useAuth();
  const { sextet, round, staffList, loading, saving, error, isLeader, moveUp, moveDown, handleSave } = usePreferencesManager(user, roundId);
  const preferencesOpen = round?.preferences_open === true;
  if (loading) return <div className="app-card app-card-pad" role="status">Carregando preferências...</div>;

  return <div className="app-page">
    <div className="app-page-head"><div><p className="app-eyebrow">Escolha dos servidores</p><h1 className="app-title">Preferências</h1><p className="app-subtitle">Ordene os servidores do mais desejado para o menos desejado.</p></div><span className="app-pill neutral">Versão {sextet?.preference_version ?? 0}</span></div>
    <div className="app-notice"><strong>Sua prioridade não muda ao editar a lista.</strong>O horário que vale para a prioridade é o da confirmação do sexteto.</div>
    {!preferencesOpen && <Alert variant="warning" title="Janela encerrada">As preferências só podem ser enviadas durante o prazo da rodada.</Alert>}
    {!isLeader && <Alert variant="warning">Apenas o líder do sexteto pode editar e salvar as preferências.</Alert>}
    {error && <Alert variant="error">{error}</Alert>}
    <section className="app-card"><div className="app-card-pad app-section-head" style={{marginBottom:0,borderBottom:'1px solid var(--line)'}}><div><div className="app-icon-bubble mb-3"><ListOrdered size={20}/></div><h2>Ranking de servidores</h2><p>{staffList.length} servidores posicionados · use as setas para alterar a ordem</p></div></div><ol>{staffList.map((staff,index) => <PreferenceListItem key={staff.id} staff={staff} index={index} totalItems={staffList.length} isLeader={isLeader && preferencesOpen} onMoveUp={moveUp} onMoveDown={moveDown}/>)}</ol></section>
    <div className="app-confirm-bar"><button type="button" onClick={handleSave} disabled={saving || !isLeader || !preferencesOpen || staffList.length === 0} className="app-button"><Save size={16}/>{saving ? 'Salvando...' : preferencesOpen ? 'Salvar preferências' : 'Preferências encerradas'}</button></div>
  </div>;
}
