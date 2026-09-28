import { ArrowUp, ArrowDown } from 'lucide-react';

export default function PreferenceListItem({ staff, index, totalItems, isLeader, onMoveUp, onMoveDown }) {
  return <li className="app-list-item"><span className="app-rank">{String(index + 1).padStart(2, '0')}</span><div><strong>{staff.name}</strong>{index === 0 && <small>Primeira preferência</small>}</div>{isLeader ? <div><button type="button" onClick={() => onMoveUp(index)} disabled={index === 0} aria-label={`Subir ${staff.name} na lista`}><ArrowUp size={16}/></button><button type="button" onClick={() => onMoveDown(index)} disabled={index === totalItems - 1} aria-label={`Descer ${staff.name} na lista`}><ArrowDown size={16}/></button></div> : <span className="app-muted text-xs">#{index + 1}</span>}</li>;
}
