import { Navigate, useParams } from 'react-router-dom';

export default function PreviousGroupRoute() {
  const { roundId } = useParams();
  return <Navigate to={`/aluno/grupo${roundId ? `/${roundId}` : ''}`} replace />;
}
