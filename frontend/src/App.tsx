// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import { HomeAluno } from './pages/aluno/HomeAluno';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* Rota 01 - Login */}
        <Route path="/login" element={<Login />} />
        
        {/* Rota 02 - Home do Aluno (Próxima etapa) */}
        <Route path="/aluno" element={<HomeAluno />} />

      </Routes>
    </BrowserRouter>
  );
}