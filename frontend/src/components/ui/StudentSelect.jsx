import { useState, useEffect, useRef } from 'react';
import { Search } from 'lucide-react';
import { api } from '../../api/api';

export function StudentSelect({ label, value, onChange, icon }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const wrapperRef = useRef(null);

  // Fecha o dropdown ao clicar fora
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Busca na API com debounce simples
  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);

      try {
        const data = await api.get(
          `/api/students?q=${encodeURIComponent(query)}`
        );

        setResults(data);
      } catch (error) {
        console.error('Erro ao buscar alunos', error);
      } finally {
        setLoading(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [query]);

  function handleSelect(student) {
    if (student.occupied) {
      return;
    }

    onChange(student);
    setQuery('');
    setIsOpen(false);
  }

  return (
    <div
      className="flex flex-col gap-1.5 w-full relative"
      ref={wrapperRef}
    >
      <label className="text-[13px] font-semibold text-gray-700 flex items-center gap-2">
        {icon}
        {label}
      </label>

      {value ? (
        <div className="flex items-center justify-between px-3 py-2 border border-green-200 bg-green-50 rounded-md text-[13px]">
          <div className="flex flex-col">
            <span className="font-medium text-gray-900">
              {value.name}
            </span>

            <span className="text-gray-500 text-xs">
              {value.login}
            </span>
          </div>

          <button
            type="button"
            onClick={() => onChange(null)}
            className="text-gray-400 hover:text-red-500 font-bold p-1"
            title="Remover"
          >
            ✕
          </button>
        </div>
      ) : (
        <div className="relative">
          <input
            type="text"
            className="w-full px-3 py-2 pl-9 border border-gray-300 rounded-md text-[13px] focus:outline-none focus:ring-1 focus:ring-[#0A3D2A] focus:border-[#0A3D2A] placeholder-gray-400"
            placeholder="Buscar aluno por nome ou prontuário..."
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
          />

          <Search
            className="absolute left-3 top-2.5 text-gray-400"
            size={16}
          />

          {isOpen && query.length >= 2 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 max-h-60 overflow-y-auto">

              {loading ? (
                <div className="p-3 text-[13px] text-gray-500 text-center">
                  Buscando...
                </div>
              ) : results.length > 0 ? (
                results.map((student) => (
                  <div
                    key={student.id}
                    onClick={() => handleSelect(student)}
                    className={`px-3 py-2 border-b border-gray-50 last:border-0 flex justify-between items-center ${
                      student.occupied
                        ? 'bg-gray-50 opacity-60 cursor-not-allowed'
                        : 'hover:bg-green-50 cursor-pointer'
                    }`}
                  >
                    <div className="flex flex-col">
                      <span className="text-[13px] font-medium text-gray-900">
                        {student.name}
                      </span>

                      <span className="text-xs text-gray-500">
                        {student.login}
                      </span>
                    </div>

                    {student.occupied && (
                      <span className="text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                        Em outro grupo
                      </span>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-3 text-[13px] text-gray-500 text-center">
                  Nenhum aluno encontrado.
                </div>
              )}

            </div>
          )}
        </div>
      )}
    </div>
  );
}