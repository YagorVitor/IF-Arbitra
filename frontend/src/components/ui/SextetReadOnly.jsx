import { Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function SextetReadOnly({ existingSextet }) {
  const navigate = useNavigate();
  const members = [...(existingSextet?.members || [])].sort((a, b) => a.slot - b.slot);

  return <><div className="app-group-grid">{[members.slice(0,3),members.slice(3)].map((group,groupIndex) => <section key={groupIndex} className={`app-group-panel ${groupIndex ? 'blue' : ''}`}><h2>TRIO {groupIndex ? 'B' : 'A'} · {group.length} {group.length === 1 ? 'integrante' : 'integrantes'}</h2>{group.length ? group.map((member,index) => <div key={member.id} className="mb-3"><span className="text-xs font-bold text-slate-600 flex gap-1 items-center">{groupIndex === 0 && index === 0 && <Star size={15} className="text-amber-500"/>}{groupIndex === 0 && index === 0 ? 'Líder' : `Participante ${groupIndex * 3 + index + 1}`}</span><div className="bg-white border border-slate-200 rounded-lg px-3 py-3 text-sm font-semibold mt-1">{member.name}</div></div>) : <p className="app-muted text-sm">Nenhum participante neste trio.</p>}</section>)}</div><div className="app-confirm-bar"><button type="button" onClick={() => navigate('/aluno')} className="app-button ghost">Voltar ao painel</button></div></>;
}
