import { useState } from 'react';
import { Star, Diamond, Info, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { StudentSelect } from '../../components/ui/StudentSelect';
export default function MeuSexteto() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const currentUser = {
    name: user?.name || 'Carregando...',
    login: user?.login || '---',
  };

  const [trioA, setTrioA] = useState([null, null]);
  const [trioB, setTrioB] = useState([null, null, null]);

  function handleConfirm() {
    // Implementar posteriormente:
    // POST /api/rounds/{round_id}/sextets
    console.log('Confirmando sexteto...');
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          Formar sexteto
        </h1>

        <p className="text-gray-500 text-sm">
          Seu sexteto deve ter exatamente 6 alunos, organizados em dois trios.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 relative">

        <div className="hidden lg:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-gray-300">
          <Plus size={32} strokeWidth={1.5} />
        </div>

        {/* Trio A */}
        <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div className="bg-green-50 border-b border-green-100 px-5 py-3">
            <h2 className="text-green-800 font-bold text-sm tracking-wide">
              TRIO A
            </h2>
          </div>

          <div className="p-5 flex flex-col gap-6">

            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-semibold text-gray-700 flex items-center gap-2">
                <Star
                  size={16}
                  className="text-yellow-500 fill-yellow-500"
                />
                Líder do sexteto (você)
              </label>

              <div className="flex items-center justify-between px-3 py-2 border border-gray-200 bg-gray-50 rounded-md text-[13px]">
                <span className="font-medium text-gray-900">
                  {currentUser.name}
                </span>

                <span className="text-gray-500">
                  {currentUser.login}
                </span>
              </div>
            </div>

            <StudentSelect
              label="Participante 2"
              value={trioA[0]}
              onChange={(student) => setTrioA([student, trioA[1]])}
            />

            <StudentSelect
              label="Participante 3"
              value={trioA[1]}
              onChange={(student) => setTrioA([trioA[0], student])}
            />
          </div>
        </div>

        {/* Trio B */}
        <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div className="bg-blue-50/50 border-b border-blue-100 px-5 py-3">
            <h2 className="text-blue-800 font-bold text-sm tracking-wide">
              TRIO B
            </h2>
          </div>

          <div className="p-5 flex flex-col gap-6">

            <StudentSelect
              label="Líder do Trio B"
              value={trioB[0]}
              onChange={(student) =>
                setTrioB([student, trioB[1], trioB[2]])
              }
              icon={
                <Diamond
                  size={14}
                  className="text-blue-500 fill-blue-500"
                />
              }
            />

            <StudentSelect
              label="Participante 5"
              value={trioB[1]}
              onChange={(student) =>
                setTrioB([trioB[0], student, trioB[2]])
              }
            />

            <StudentSelect
              label="Participante 6"
              value={trioB[2]}
              onChange={(student) =>
                setTrioB([trioB[0], trioB[1], student])
              }
            />
          </div>
        </div>
      </div>

      {/* Ações */}
      <div className="mt-8 flex flex-col items-end gap-6">

        <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-3 max-w-2xl w-full">
          <Info
            className="text-blue-600 shrink-0 mt-0.5"
            size={20}
          />

          <div className="flex flex-col gap-1">
            <h4 className="text-sm font-bold text-blue-900">
              Antes de confirmar
            </h4>

            <p className="text-[13px] text-blue-800 leading-relaxed">
              A confirmação deste sexteto define sua prioridade na rodada.
              <br />
              Depois da confirmação, alterações não estão disponíveis nesta versão do processo.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/aluno')}
            className="px-5 py-2 rounded-md text-[14px] font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>

          <button
            onClick={handleConfirm}
            className="px-5 py-2 rounded-md text-[14px] font-medium text-white bg-[#0A3D2A] hover:bg-[#072a1d] transition-colors shadow-sm"
          >
            Confirmar sexteto
          </button>
        </div>
      </div>
    </div>
  );
}
