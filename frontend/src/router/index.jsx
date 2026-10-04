import { createBrowserRouter, Navigate, useRouteError } from "react-router-dom";
import ProtectedRoute from './ProtectedRoute';
import PreviousGroupRoute from '../components/layout/PreviousGroupRoute';

// Layouts
import AuthLayout from '../layouts/AuthLayout';
import DashboardLayout from "../layouts/DashboardLayout";

import Login from "../pages/Auth/Login";

const page = (loader) => async () => ({ Component: (await loader()).default });

function AdminRouteError() {
    const error = useRouteError();
    const failedChunk = /failed to fetch dynamically imported module|importing a module script failed/i
        .test(error?.message ?? '');

    return (
        <main className="flex min-h-screen items-center justify-center bg-[#f3f7f4] p-5 text-slate-900">
            <section role="alert" className="w-full max-w-xl rounded-2xl border border-emerald-900/10 bg-white p-7 shadow-sm sm:p-9">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-800">IF-Arbitra · Administração</p>
                <h1 className="mt-3 text-2xl font-semibold tracking-tight">
                    {failedChunk ? 'Esta tela precisa ser atualizada' : 'Não foi possível abrir esta tela'}
                </h1>
                <p className="mt-3 leading-6 text-slate-600">
                    {failedChunk
                        ? 'O sistema recebeu uma atualização enquanto esta página estava aberta. Atualize para carregar a versão mais recente.'
                        : 'Ocorreu um problema ao carregar o conteúdo. Atualize a página para tentar novamente.'}
                </p>
                <button
                    className="mt-6 min-h-11 rounded-lg bg-emerald-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
                    onClick={() => window.location.reload()}
                    type="button"
                >
                    Atualizar página
                </button>
            </section>
        </main>
    );
}

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
                        path: '/aluno/grupo',
                        lazy: page(() => import('../pages/aluno/MeuGrupo'))
                    },
                    {
                        path: '/aluno/grupo/:roundId',
                        lazy: page(() => import('../pages/aluno/MeuGrupo'))
                    },
                    {
                        path: '/aluno/sexteto',
                        element: <PreviousGroupRoute />
                    },
                    { path: '/aluno/trio', element: <PreviousGroupRoute /> },
                    { path: '/aluno/trio/:roundId', element: <PreviousGroupRoute /> },
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
                errorElement: <AdminRouteError />,
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
