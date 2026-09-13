import { ArrowUp, ArrowDown } from 'lucide-react';

export default function PreferenceListItem({ 
  staff, 
  index, 
  totalItems, 
  isLeader, 
  onMoveUp, 
  onMoveDown 
}) {
  return (
    <li className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center gap-4">
        <span className="w-6 text-center font-semibold text-gray-400">{index + 1}</span>
        <span className="font-medium text-gray-900">{staff.name}</span>
        {index === 0 && (
          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
            Primeira preferência
          </span>
        )}
      </div>
      
      {isLeader && (
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onMoveUp(index)}
            disabled={index === 0}
            className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded disabled:opacity-30 disabled:hover:bg-transparent"
            aria-label="Mover para cima"
          >
            <ArrowUp className="w-5 h-5" />
          </button>
          <button
            type="button"
            onClick={() => onMoveDown(index)}
            disabled={index === totalItems - 1}
            className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded disabled:opacity-30 disabled:hover:bg-transparent"
            aria-label="Mover para baixo"
          >
            <ArrowDown className="w-5 h-5" />
          </button>
        </div>
      )}
    </li>
  );
}