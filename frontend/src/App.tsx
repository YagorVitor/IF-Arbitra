// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { HomeAluno } from './pages/aluno/HomeAluno';
import { MeuSexteto } from './pages/aluno/MeuSexteto';
import Login from './pages/Login';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/aluno" element={<HomeAluno />} />
          <Route path="/aluno/sexteto" element={<MeuSexteto />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}