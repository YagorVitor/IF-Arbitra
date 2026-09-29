import { useState } from 'react';
import { Crown, Info, UsersRound } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { StudentSelect } from './StudentSelect';

export default function TrioForm({ currentUser, onSubmit, isSubmitting, setError }) {
  const navigate = useNavigate();
  const [selected, setSelected] = useState([null, null]);

  function changeMember(index, student) {
    setSelected((previous) => previous.map((member, i) => i === index ? student : member));
  }

  function handleConfirm() {
    if (!selected[0] || !selected[1]) {
      setError('Selecione os participantes 2 e 3 para formar o trio.');
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
      <div className="app-group-grid app-trio-form">
        <section className="app-group-panel"><h2><UsersRound size={17} className="inline mr-2"/>SEU TRIO</h2>
          <div className="flex flex-col gap-1.5 mb-3"><span className="text-[13px] font-semibold text-gray-700 flex items-center gap-2"><Crown size={16} className="text-amber-500"/>Líder do trio (você)</span><div className="flex flex-col px-3 py-2 border border-green-200 bg-white rounded-md text-[13px]"><strong>{currentUser.name}</strong><span className="text-gray-500 text-xs">{currentUser.login}</span></div></div>
          {selected.map((student,index) => <StudentSelect key={index} label={`Participante ${index + 2} · obrigatório`} value={student} onChange={(value) => changeMember(index,value)}/>)}</section>
      </div>

      <div className="mt-5 flex flex-col items-end gap-5">
        <div className="app-notice flex gap-3 w-full">
          <Info className="text-blue-600 shrink-0 mt-0.5" size={20} />
          <div className="flex flex-col gap-1">
            <h4 className="text-sm font-bold text-blue-900">Antes de confirmar</h4>
            <p className="text-[13px] text-blue-800 leading-relaxed">
              A confirmação do trio define sua prioridade na rodada. Depois disso, os integrantes não podem ser alterados. O sistema reunirá seu trio a outro durante a alocação.
            </p>
          </div>
        </div>
        <div className="app-confirm-bar">
          <button type="button" onClick={() => navigate('/aluno')} className="app-button ghost">
            Cancelar
          </button>
          <button type="button" disabled={isSubmitting} onClick={handleConfirm} className="app-button">
            {isSubmitting ? 'Confirmando...' : 'Confirmar trio'}
          </button>
        </div>
      </div>
    </>
  );
}
