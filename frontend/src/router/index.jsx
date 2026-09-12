import { createBrowserRouter, Navigate } from "react-router-dom";
import ProtectedRoute from './ProtectedRoute'

//Layouts
import AuthLayout from '../layouts/AuthLayout'
import DashboardLayout from "../layouts/DashboardLayout";

//Pages
import Login from "../pages/Auth/Login";
import HomeAluno from "../pages/aluno/HomeAluno";
import MeuSexteto from "../pages/aluno/MeuSexteto";

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
        element: <ProtectedRoute/>,
        children: [
            {
                path: '/aluno',
                element:<DashboardLayout/>,
                children: [
                    {
                        index: true,
                        element: <HomeAluno/>,
                    },
                    {
                        path: '/aluno/sexteto',
                        element: <MeuSexteto/>
                    }
                ]
            }
        ]
    }
])