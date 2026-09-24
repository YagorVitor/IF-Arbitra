import { useState } from 'react';
import { Star, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { StudentSelect } from './StudentSelect';

export default function SextetForm({ currentUser, onSubmit, isSubmitting, setError }) {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(Array(5).fill(null));

  function changeMember(index, student) {
    setSelected((previous) => previous.map((member, i) => i === index ? student : member));
  }

  function handleConfirm() {
    if (!selected[0] || !selected[1]) {
      setError('Selecione os participantes 2 e 3 para formar um grupo de pelo menos 3 alunos.');
      return;
    }
    if (selected.some((member, index) => !member && selected.slice(index + 1).some(Boolean))) {
      setError('Preencha os participantes em ordem, sem deixar posições vazias entre eles.');
      return;
    }
    const memberIds = [currentUser.id, ...selected.filter(Boolean).map((student) => student.id)];
    if (new Set(memberIds).size !== memberIds.length) {
      setError('O grupo não pode conter integrantes repetidos.');
      return;
    }
    onSubmit(memberIds);
  }

  return (
    <>
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
        <div className="bg-green-50 border-b border-green-100 px-5 py-3">
          <h2 className="text-green-800 font-bold text-sm tracking-wide">INTEGRANTES · 3 A 6 ALUNOS</h2>
        </div>
        <div className="p-5 grid gap-6 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <label className="text-[13px] font-semibold text-gray-700 flex items-center gap-2">
              <Star size={16} className="text-yellow-500 fill-yellow-500" />
              Líder do grupo (você)
            </label>
            <div className="flex flex-col px-3 py-2 border border-gray-200 bg-gray-50 rounded-md text-[13px]">
              <span className="font-medium text-gray-900">{currentUser.name}</span>
              <span className="text-gray-500 text-xs">{currentUser.login}</span>
            </div>
          </div>
          {selected.map((student, index) => (
            <StudentSelect
              key={index}
              label={`Participante ${index + 2}${index < 2 ? ' · obrigatório' : ' · opcional'}`}
              value={student}
              onChange={(value) => changeMember(index, value)}
            />
          ))}
        </div>
      </div>

      <div className="mt-8 flex flex-col items-end gap-6">
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-3 max-w-2xl w-full">
          <Info className="text-blue-600 shrink-0 mt-0.5" size={20} />
          <div className="flex flex-col gap-1">
            <h4 className="text-sm font-bold text-blue-900">Antes de confirmar</h4>
            <p className="text-[13px] text-blue-800 leading-relaxed">
              A confirmação do grupo define sua prioridade na rodada. Depois disso, os integrantes não podem ser alterados.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => navigate('/aluno')} className="px-5 py-2 rounded-md text-[14px] font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors">
            Cancelar
          </button>
          <button type="button" disabled={isSubmitting} onClick={handleConfirm} className="px-5 py-2 rounded-md text-[14px] font-medium text-white bg-[#0A3D2A] hover:bg-[#072a1d] transition-colors shadow-sm disabled:opacity-50">
            {isSubmitting ? 'Confirmando...' : 'Confirmar grupo'}
          </button>
        </div>
      </div>
    </>
  );
}
