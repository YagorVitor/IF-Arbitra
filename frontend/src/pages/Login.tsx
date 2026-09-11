// frontend/src/pages/Login.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

interface UserResponse {
  id: string;
  name: string;
  login: string;
  role: 'STUDENT' | 'ADMIN';
}

export default function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { setUser } = useAuth();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const userData = await api.post<UserResponse>('/api/auth/login', {
        login: identifier,
        password: password,
      });

      setUser(userData); // Salva globalmente

      if (userData.role === 'STUDENT') {
        navigate('/aluno');
      } else {
        navigate('/admin');
      }
    } catch (err: any) {
      const apiError = err as ApiError;
      setError(apiError.message || 'Credenciais inválidas ou erro de comunicação.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A3D2A] flex flex-col items-center justify-center font-sans relative">
      
      {/* Top Branding */}
      <div className="flex flex-col items-center mb-8">
        <div className="grid grid-cols-3 gap-[3px] mb-4">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="w-[10px] h-[10px] bg-white rounded-[2px] opacity-90"></div>
          ))}
        </div>
        <h1 className="text-white text-[22px] font-bold tracking-wide">
          IF-Arbitra
        </h1>
        <p className="text-green-100/80 text-[13px] font-medium mt-0.5">
          Instituto Federal
        </p>
      </div>

      {/* Main Card */}
      <div className="bg-white w-full max-w-[340px] rounded-[10px] shadow-2xl p-8 z-10">
        <div className="text-center mb-7">
          <h2 className="text-[22px] font-bold text-gray-900">IF-Arbitra</h2>
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
            <input
              id="password"
              type="password"
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
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              'Entrar'
            )}
          </button>
        </form>
      </div>

      {/* Footer Branding */}
      <div className="absolute bottom-6 text-green-100/60 text-[12px] font-medium tracking-wide">
        Instituto Federal
      </div>
    </div>
  );
}