import { Crown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function GroupReadOnly({ existingGroup, trioMode = false }) {
  const navigate = useNavigate();
  const members = [...(existingGroup?.members || [])].sort((a, b) => a.slot - b.slot);

  return (
    <>
      <section className="app-group-panel app-trio-members">
        <h2>{'PARTICIPANTES REGISTRADOS'} · {members.length} integrantes</h2>
        <ol className="app-member-list">
          {members.map((member, index) => (
            <li key={member.id} className="app-member">
              <span className="app-member-number" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
              <div><span className="app-label">{index === 0 ? 'Capitão' : `Participante ${index + 1}`}</span><strong>{member.name}</strong></div>
              {index === 0 && <Crown size={18} aria-hidden="true" />}
            </li>
          ))}
        </ol>
      </section>
      {trioMode && <p className="app-notice">O sistema reunirá seu trio a outro conforme as preferências. A composição final ficará disponível após a publicação do resultado.</p>}
      <div className="app-confirm-bar"><button type="button" onClick={() => navigate('/aluno')} className="app-button ghost">Voltar ao painel</button></div>
    </>
  );
}
