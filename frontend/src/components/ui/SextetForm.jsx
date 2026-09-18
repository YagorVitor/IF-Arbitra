import { useState } from 'react';
import { Star, Diamond, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { StudentSelect } from './StudentSelect';

export default function SextetForm({ currentUser, onSubmit, isSubmitting, error, setError }) {
  const navigate = useNavigate();
  const [trioA, setTrioA] = useState([null, null]);
  const [trioB, setTrioB] = useState([null, null, null]);

  function handleConfirm() {
    if (!trioA[0] || !trioA[1] || !trioB[0] || !trioB[1] || !trioB[2]) {
      setError('Por favor, seleciona todos os 6 integrantes do sexteto.');
      return;
    }
    
    const memberIds = [currentUser.id, trioA[0].id, trioA[1].id, trioB[0].id, trioB[1].id, trioB[2].id];
    if (new Set(memberIds).size !== 6) {
      setError('O sexteto não pode conter membros duplicados.');
      return;
    }

    onSubmit(memberIds);
  }

  return (
    <>
      <div className="flex flex-col lg:flex-row gap-6 relative">
        {/* Trio A */}
        <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div className="bg-green-50 border-b border-green-100 px-5 py-3">
            <h2 className="text-green-800 font-bold text-sm tracking-wide">TRIO A</h2>
          </div>
          <div className="p-5 flex flex-col gap-6">
            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-semibold text-gray-700 flex items-center gap-2">
                <Star size={16} className="text-yellow-500 fill-yellow-500" />
                Líder do sexteto (tu)
              </label>
              <div className="flex items-center justify-between px-3 py-2 border border-gray-200 bg-gray-50 rounded-md text-[13px]">
                <span className="font-medium text-gray-900">{currentUser.name}</span>
                <span className="text-gray-500">{currentUser.login}</span>
              </div>
            </div>
            <StudentSelect label="Participante 2" value={trioA[0]} onChange={(s) => setTrioA([s, trioA[1]])} />
            <StudentSelect label="Participante 3" value={trioA[1]} onChange={(s) => setTrioA([trioA[0], s])} />
          </div>
        </div>

        {/* Trio B */}
        <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div className="bg-blue-50/50 border-b border-blue-100 px-5 py-3">
            <h2 className="text-blue-800 font-bold text-sm tracking-wide">TRIO B</h2>
          </div>
          <div className="p-5 flex flex-col gap-6">
            <StudentSelect label="Líder do Trio B" value={trioB[0]} onChange={(s) => setTrioB([s, trioB[1], trioB[2]])} icon={<Diamond size={14} className="text-blue-500 fill-blue-500" />} />
            <StudentSelect label="Participante 5" value={trioB[1]} onChange={(s) => setTrioB([trioB[0], s, trioB[2]])} />
            <StudentSelect label="Participante 6" value={trioB[2]} onChange={(s) => setTrioB([trioB[0], trioB[1], s])} />
          </div>
        </div>
      </div>

      <div className="mt-8 flex flex-col items-end gap-6">
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-3 max-w-2xl w-full">
          <Info className="text-blue-600 shrink-0 mt-0.5" size={20} />
          <div className="flex flex-col gap-1">
            <h4 className="text-sm font-bold text-blue-900">Antes de confirmar</h4>
            <p className="text-[13px] text-blue-800 leading-relaxed">
              A confirmação deste sexteto define a tua prioridade na rodada. Depois da confirmação, as alterações não estão disponíveis.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => navigate('/aluno')} className="px-5 py-2 rounded-md text-[14px] font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors">
            Cancelar
          </button>
          <button type="button" disabled={isSubmitting} onClick={handleConfirm} className="px-5 py-2 rounded-md text-[14px] font-medium text-white bg-[#0A3D2A] hover:bg-[#072a1d] transition-colors shadow-sm disabled:opacity-50">
            {isSubmitting ? 'A confirmar...' : 'Confirmar sexteto'}
          </button>
        </div>
      </div>
    </>
  );
}