// frontend/src/pages/HomeAluno.tsx
import React from 'react';
import { AppLayout } from '../../components/layout/AppLayout';
import { CheckCircle2, CircleDashed } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function HomeAluno() {
  const navigate = useNavigate();

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header Section */}
        <div className="flex items-start justify-between mb-10">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Processo de alocação 2026/2</h1>
            <p className="text-gray-500 text-sm">Formação dos sextetos e escolha dos servidores</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-green-50 text-green-700 rounded-full text-xs font-semibold border border-green-100">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            Em andamento
          </div>
        </div>

        {/* Stepper / Timeline */}
        <div className="mb-12">
          <div className="flex items-center justify-between relative">
            {/* Linha de fundo conectando os steps */}
            <div className="absolute top-4 left-0 w-full h-[2px] bg-gray-200 -z-10"></div>
            
            {/* Linha verde de progresso (calculada para 33% = step 1 to 2) */}
            <div className="absolute top-4 left-0 w-1/3 h-[2px] bg-green-600 -z-10"></div>

            {/* Step 1 */}
            <div className="flex flex-col items-center bg-white px-2">
              <div className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center font-bold text-xs border-2 border-green-600 mb-2">
                01
              </div>
              <span className="text-xs font-bold text-green-700 mb-0.5">Sexteto</span>
              <span className="text-[10px] text-gray-500">Concluído</span>
            </div>

            {/* Step 2 */}
            <div className="flex flex-col items-center bg-white px-2">
              <div className="w-8 h-8 rounded-full bg-[#0A3D2A] text-white flex items-center justify-center font-bold text-xs border-2 border-[#0A3D2A] mb-2 shadow-[0_0_0_3px_rgba(10,61,42,0.1)]">
                02
              </div>
              <span className="text-xs font-bold text-gray-900 mb-0.5">Preferências</span>
              <span className="text-[10px] text-gray-500">Em andamento</span>
            </div>

            {/* Step 3 */}
            <div className="flex flex-col items-center bg-white px-2 opacity-50">
              <div className="w-8 h-8 rounded-full bg-gray-50 text-gray-400 flex items-center justify-center font-bold text-xs border-2 border-gray-300 mb-2">
                03
              </div>
              <span className="text-xs font-medium text-gray-500 mb-0.5">Processamento</span>
              <span className="text-[10px] text-gray-400">Bloqueado</span>
            </div>

            {/* Step 4 */}
            <div className="flex flex-col items-center bg-white px-2 opacity-50">
              <div className="w-8 h-8 rounded-full bg-gray-50 text-gray-400 flex items-center justify-center font-bold text-xs border-2 border-gray-300 mb-2">
                04
              </div>
              <span className="text-xs font-medium text-gray-500 mb-0.5">Resultado</span>
              <span className="text-[10px] text-gray-400">Bloqueado</span>
            </div>
          </div>
        </div>

        {/* Current Stage Highlight */}
        <div className="mb-8">
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Etapa Atual</p>
          <div className="flex items-center justify-between border-b border-gray-200 pb-4">
            <h2 className="text-xl font-bold text-gray-900">Preferências</h2>
            <div className="text-right">
              <div className="text-xl font-bold text-gray-900">03d 12h</div>
              <div className="text-xs text-gray-500">Encerra em 13 set às 18:00</div>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Card Sexteto */}
          <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-gray-900">Sexteto</h3>
              <div className="flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-md">
                <CheckCircle2 size={14} className="text-green-600" />
                Confirmado
              </div>
            </div>
            
            <div className="flex justify-between items-end">
              <div>
                <p className="text-xs text-gray-500 mb-1">Sua prioridade</p>
                <p className="text-lg font-bold text-gray-900">#07</p>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
              <span>Confirmado em</span>
              <span>10/09/2026 14:32:18</span>
            </div>
          </div>

          {/* Card Preferências */}
          <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-gray-900">Preferências</h3>
              <div className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-md">
                Versão 3
              </div>
            </div>
            
            <div className="flex justify-between items-end mb-4">
              <div>
                <p className="text-xs text-gray-500 mb-1">14 de 14 ordenadas</p>
                <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden mt-2">
                  <div className="w-full h-full bg-green-600 rounded-full"></div>
                </div>
              </div>
            </div>

            <button 
              onClick={() => navigate('/aluno/preferencias')}
              className="w-full py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200"
            >
              Revisar preferências
            </button>
          </div>

        </div>
      </div>
    </AppLayout>
  );
}