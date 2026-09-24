import { Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function SextetReadOnly({ existingSextet }) {
  const navigate = useNavigate();
  const members = [...(existingSextet?.members || [])].sort((a, b) => a.slot - b.slot);

  return (
    <>
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
        <div className="bg-green-50 border-b border-green-100 px-5 py-3">
          <h2 className="text-green-800 font-bold text-sm tracking-wide">{members.length} INTEGRANTES CONFIRMADOS</h2>
        </div>
        <div className="p-5 grid gap-6 sm:grid-cols-2">
          {members.map((member, index) => (
            <div key={member.id} className="flex flex-col gap-1.5">
              <span className="text-[13px] font-semibold text-gray-700 flex items-center gap-2">
                {index === 0 && <Star size={16} className="text-yellow-500 fill-yellow-500" />}
                {index === 0 ? 'Líder do grupo' : `Participante ${index + 1}`}
              </span>
              <div className="px-3 py-2 border border-gray-200 bg-gray-50 rounded-md text-[13px] font-medium text-gray-900">
                {member.name}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-8 flex justify-end">
        <button type="button" onClick={() => navigate('/aluno')} className="px-5 py-2 rounded-md text-[14px] font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors">
          Voltar ao painel
        </button>
      </div>
    </>
  );
}
