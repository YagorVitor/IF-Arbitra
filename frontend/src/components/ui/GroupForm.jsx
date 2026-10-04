import { useState } from 'react';
import { Crown, Info, UsersRound } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { StudentSelect } from './StudentSelect';

export default function GroupForm({ currentUser, round, onSubmit, isSubmitting, setError }) {
  const navigate = useNavigate();
  const [selected, setSelected] = useState([null, null, null, null, null, null]);

  function changeMember(index, student) {
    setSelected((previous) => previous.map((member, i) => i === index ? student : member));
  }

  function handleConfirm() {
    if (selected.slice(0, 4).some((student) => !student)) {
      setError('Selecione pelo menos quatro integrantes além do capitão.');
      return;
    }
    const memberIds = [currentUser.id, ...selected.filter(Boolean).map((student) => student.id)];
    if (new Set(memberIds).size !== memberIds.length) {
      setError('O grupo não pode conter integrantes repetidos.');
      return;
    }
    if (memberIds.length <= 6 && round.registered_six >= 3) { setError('As três vagas para grupos de cinco ou seis foram preenchidas.'); return; }
    if (memberIds.length === 7 && round.registered_seven >= 8) { setError('As oito vagas para grupos de sete foram preenchidas. Forme um grupo de seis, se houver vaga.'); return; }
    onSubmit(memberIds);
  }

  return (
    <>
      <p className="app-notice mb-4">Vagas preenchidas: {round.registered_six} de 3 grupos com 5 ou 6 integrantes e {round.registered_seven} de 8 grupos com 7.</p>
      <div className="app-group-grid app-trio-form">
        <section className="app-group-panel"><h2><UsersRound size={17} className="inline mr-2"/>SEU GRUPO</h2>
          <div className="flex flex-col gap-1.5 mb-3"><span className="text-[13px] font-semibold text-gray-700 flex items-center gap-2"><Crown size={16} className="text-amber-500"/>Capitão (você)</span><div className="flex flex-col px-3 py-2 border border-green-200 bg-white rounded-md text-[13px]"><strong>{currentUser.name}</strong><span className="text-gray-500 text-xs">{currentUser.login}</span></div></div>
          <div className="grid gap-4 sm:grid-cols-2">{selected.map((student,index) => <StudentSelect key={index} label={`Participante ${index + 2} · ${index < 4 ? 'obrigatório' : 'opcional'}`} value={student} onChange={(value) => changeMember(index,value)}/>)}</div></section>
      </div>

      <div className="mt-5 flex flex-col items-end gap-5">
        <div className="app-notice flex gap-3 w-full">
          <Info className="text-blue-600 shrink-0 mt-0.5" size={20} />
          <div className="flex flex-col gap-1">
            <h4 className="text-sm font-bold text-blue-900">Antes de confirmar</h4>
            <p className="text-[13px] text-blue-800 leading-relaxed">
              Você é o capitão e conta entre os cinco integrantes mínimos. Depois, pode incluir até mais duas pessoas. A confirmação define a prioridade; depois dela, a composição fica registrada e não pode ser alterada.
            </p>
          </div>
        </div>
        <div className="app-confirm-bar">
          <button type="button" onClick={() => navigate('/aluno')} className="app-button ghost">
            Cancelar
          </button>
          <button type="button" disabled={isSubmitting} onClick={handleConfirm} className="app-button">
            {isSubmitting ? 'Confirmando...' : 'Confirmar grupo e continuar'}
          </button>
        </div>
      </div>
    </>
  );
}
