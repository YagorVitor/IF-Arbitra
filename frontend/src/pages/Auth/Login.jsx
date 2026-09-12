import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

import PasswordInput from './components/PasswordInput';

export default function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const navigate = useNavigate();
  const { login } = useAuth();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try{
      const userData = await login(identifier, password);

      if (userData.role === 'STUDENT') {
        navigate('/aluno');
      } else {
        navigate('/admin');
      }

    } catch(error){
      setError(error.message || 'Credenciais inválidas ou erro de comunicação.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white w-full max-w-[340px] rounded-[10px] shadow-2xl p-8">
        <div className="text-center mb-7">
            <h2 className="text-[22px] font-bold text-gray-900">
            IF-Arbitra
            </h2>

            <p className="text-gray-500 text-[13px] mt-1.5 leading-[1.4]">
            Processo institucional de <br />
            formação e alocação de grupos
            </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
            <div className="p-3 bg-red-50 text-red-600 text-xs rounded-md border border-red-100 text-center">
                {error}
            </div>
            )}

            <div className="flex flex-col gap-1.5">
            <label
                htmlFor="identifier"
                className="text-[13px] font-medium text-gray-700"
            >
                Identificador
            </label>

            <input
                id="identifier"
                type="text"
                placeholder="AQ3021416"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
                className="w-full px-3 py-2.5 border border-gray-300 rounded-md text-[13px] text-gray-900 focus:outline-none focus:ring-1 focus:ring-[#0A3D2A] focus:border-[#0A3D2A] placeholder-gray-400 transition-colors"
            />
            </div>

            <div className="flex flex-col gap-1.5">
            <label
                htmlFor="password"
                className="text-[13px] font-medium text-gray-700"
            >
                Senha
            </label>

            <PasswordInput
              id="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2.5 border border-gray-300 rounded-md text-[13px] text-gray-900 focus:outline-none focus:ring-1 focus:ring-[#0A3D2A] focus:border-[#0A3D2A] placeholder-gray-400 transition-colors"
            />
            </div>

            <button
            type="submit"
            disabled={loading}
            className="mt-2 w-full bg-[#0A3D2A] hover:bg-[#072a1d] text-white text-[14px] font-medium py-2.5 rounded-md transition-colors flex justify-center items-center h-[42px] disabled:opacity-70 disabled:cursor-not-allowed"
            >
            {loading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
                'Entrar'
            )}
            </button>
        </form>
    </div>
  );
}