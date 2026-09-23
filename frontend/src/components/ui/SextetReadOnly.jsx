import { Star, Diamond } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function ReadOnlyMemberCard({ label, member, icon }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[13px] font-semibold text-gray-700 flex items-center gap-2">
        {icon} {label}
      </label>
      <div className="flex items-center justify-between px-3 py-2 border border-gray-200 bg-gray-50 rounded-md text-[13px]">
        <span className="font-medium text-gray-900">{member?.name || '---'}</span>
      </div>
    </div>
  );
}

export default function SextetReadOnly({ existingSextet }) {
  const navigate = useNavigate();
  
  const getMemberBySlot = (slotIndex) => {
    return existingSextet?.members?.find((m) => m.slot === slotIndex) || null;
  };

  return (
    <>
      <div className="flex flex-col lg:flex-row gap-6 relative">
        <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div className="bg-green-50 border-b border-green-100 px-5 py-3">
            <h2 className="text-green-800 font-bold text-sm tracking-wide">TRIO A</h2>
          </div>
          <div className="p-5 flex flex-col gap-6">
            <ReadOnlyMemberCard label="Líder do sexteto (tu)" member={getMemberBySlot(0)} icon={<Star size={16} className="text-yellow-500 fill-yellow-500" />} />
            <ReadOnlyMemberCard label="Participante 2" member={getMemberBySlot(1)} />
            <ReadOnlyMemberCard label="Participante 3" member={getMemberBySlot(2)} />
          </div>
        </div>

        <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div className="bg-blue-50/50 border-b border-blue-100 px-5 py-3">
            <h2 className="text-blue-800 font-bold text-sm tracking-wide">TRIO B</h2>
          </div>
          <div className="p-5 flex flex-col gap-6">
            <ReadOnlyMemberCard label="Líder do Trio B" member={getMemberBySlot(3)} icon={<Diamond size={14} className="text-blue-500 fill-blue-500" />} />
            <ReadOnlyMemberCard label="Participante 5" member={getMemberBySlot(4)} />
            <ReadOnlyMemberCard label="Participante 6" member={getMemberBySlot(5)} />
          </div>
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