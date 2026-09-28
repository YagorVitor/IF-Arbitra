import { Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from './Button';

export default function ResultUnpublished({ roundName }) {
  const navigate = useNavigate();

  return (
    <div className="app-card app-card-pad text-center flex flex-col items-center py-12">
      <Clock className="w-12 h-12 text-blue-500 mb-4" />
      <h2 className="text-lg font-semibold text-gray-900 mb-2">Resultados em processamento</h2>
      <p className="text-gray-600 mb-6 max-w-md">
        A alocação para a rodada "{roundName}" ainda não foi publicada pela administração. Volte mais tarde.
      </p>
      <Button onClick={() => navigate('/aluno')} variant="outline">
        Voltar ao Início
      </Button>
    </div>
  );
}
