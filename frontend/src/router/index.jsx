import { createBrowserRouter, Navigate } from "react-router-dom";
import ProtectedRoute from './ProtectedRoute';

// Layouts
import AuthLayout from '../layouts/AuthLayout';
import DashboardLayout from "../layouts/DashboardLayout";

// Pages
import Login from "../pages/Auth/Login";
import HomeAluno from "../pages/aluno/HomeAluno";
import MeuSexteto from "../pages/aluno/MeuSexteto";
import Preferencias from "../pages/aluno/Preferencias";
import ResultadoAluno from "../pages/aluno/ResultadoAluno";
import AdminCadastros from '../pages/admin/AdminCadastros';
import AdminRodadas from '../pages/admin/AdminRodadas';
import AdminAuditoria from '../pages/admin/AdminAuditoria';

export const router = createBrowserRouter([
    {
        path: '/',
        element: <Navigate to={'/auth'} replace />,
    },
    {
        path: '/auth',
        element: <AuthLayout/>,
        children: [
            {
                index: true,
                element: <Login/>
            },
        ]
    },
    {
        element: <ProtectedRoute role="STUDENT"/>,
        children: [
            {
                path: '/aluno',
                element: <DashboardLayout/>,
                children: [
                    {
                        index: true,
                        element: <HomeAluno/>,
                    },
                    {
                        path: '/aluno/sexteto',
                        element: <MeuSexteto/>
                    },
                    {
                        path: '/aluno/sexteto/:roundId',
                        element: <MeuSexteto/>
                    },
                    {
                        path: '/aluno/preferencias',
                        element: <Preferencias/>
                    },
                    {
                        path: '/aluno/preferencias/:roundId',
                        element: <Preferencias/>
                    },
                    {
                        path: '/aluno/resultado',
                        element: <ResultadoAluno/>
                    },
                    {
                        path: '/aluno/resultado/:roundId',
                        element: <ResultadoAluno/>
                    }
                ]
            }
        ]
    },
    {
        element: <ProtectedRoute role="ADMIN"/>,
        children: [
            {
                path: '/admin',
                element: <DashboardLayout/>,
                children: [
                    { index: true, element: <AdminRodadas/> },
                    { path: 'cadastros', element: <AdminCadastros/> },
                    { path: 'auditoria', element: <AdminAuditoria/> },
                ],
            },
        ],
    },
]);
