import { createBrowserRouter, Navigate } from "react-router-dom";
import ProtectedRoute from './ProtectedRoute';
import PreviousGroupRoute from '../components/layout/PreviousGroupRoute';

// Layouts
import AuthLayout from '../layouts/AuthLayout';
import DashboardLayout from "../layouts/DashboardLayout";

import Login from "../pages/Auth/Login";

const page = (loader) => async () => ({ Component: (await loader()).default });

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
                        lazy: page(() => import('../pages/aluno/HomeAluno')),
                    },
                    {
                        path: '/aluno/trio',
                        lazy: page(() => import('../pages/aluno/MeuTrio'))
                    },
                    {
                        path: '/aluno/trio/:roundId',
                        lazy: page(() => import('../pages/aluno/MeuTrio'))
                    },
                    {
                        path: '/aluno/sexteto',
                        element: <PreviousGroupRoute />
                    },
                    {
                        path: '/aluno/sexteto/:roundId',
                        element: <PreviousGroupRoute />
                    },
                    {
                        path: '/aluno/preferencias',
                        lazy: page(() => import('../pages/aluno/Preferencias'))
                    },
                    {
                        path: '/aluno/preferencias/:roundId',
                        lazy: page(() => import('../pages/aluno/Preferencias'))
                    },
                    {
                        path: '/aluno/resultado',
                        lazy: page(() => import('../pages/aluno/ResultadoAluno'))
                    },
                    {
                        path: '/aluno/resultado/:roundId',
                        lazy: page(() => import('../pages/aluno/ResultadoAluno'))
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
                    { index: true, lazy: page(() => import('../pages/admin/AdminOverview')) },
                    { path: 'rodadas', lazy: page(() => import('../pages/admin/AdminRodadas')) },
                    { path: 'cadastros', lazy: page(() => import('../pages/admin/AdminCadastros')) },
                    { path: 'auditoria', lazy: page(() => import('../pages/admin/AdminAuditoria')) },
                ],
            },
        ],
    },
]);
