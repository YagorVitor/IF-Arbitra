import { useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { usePreferencesManager } from '../../hooks/usePreferencesManager';

import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import PreferenceListItem from '../../components/ui/PreferenceListItem';

export default function Preferencias() {
  const { roundId: paramRoundId } = useParams();
  const { user } = useAuth();

  const {
    sextet,
    staffList,
    loading,
    saving,
    error,
    isLeader,
    moveUp,
    moveDown,
    handleSave,
  } = usePreferencesManager(user, paramRoundId);

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Carregando preferências...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Preferências de servidores</h1>
        <p className="text-gray-600 mt-1">Ordene do servidor que seu sexteto mais deseja para o menos desejado.</p>
      </div>

      <Alert variant="info" title="Sua prioridade não muda ao editar preferências.">
        O horário considerado é o da confirmação do sexteto, não o horário desta lista.
      </Alert>

      {!isLeader && (
        <Alert variant="warning">
          Apenas o líder do Trio A pode editar e salvar as preferências do sexteto.
        </Alert>
      )}

      {error && <Alert variant="error">{error}</Alert>}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
        <div className="flex justify-between items-center p-4 border-b border-gray-200 bg-gray-50 text-sm font-medium text-gray-700">
          <span>{staffList.length} de {staffList.length} posicionados</span>
          <span>Versão {sextet?.preference_version ?? 0}</span>
        </div>

        <ul className="divide-y divide-gray-100">
          {staffList.map((staff, index) => (
            <PreferenceListItem
              key={staff.id}
              staff={staff}
              index={index}
              totalItems={staffList.length}
              isLeader={isLeader}
              onMoveUp={moveUp}
              onMoveDown={moveDown}
            />
          ))}
        </ul>
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} disabled={saving || !isLeader} className="w-full sm:w-auto">
          {saving ? 'Salvando...' : 'Salvar preferências'}
        </Button>
      </div>
    </div>
  );
}