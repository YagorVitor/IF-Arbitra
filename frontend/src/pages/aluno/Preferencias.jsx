import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { roundService } from '../../services/roundService';
import { sextetService } from '../../services/sextetService';

import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import PreferenceListItem from '../../components/ui/PreferenceListItem';

export default function Preferencias() {
  const { roundId: paramRoundId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [sextet, setSextet] = useState(null);
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true);
        
        const targetRound = paramRoundId 
          ? await roundService.getById(paramRoundId)
          : await roundService.getActiveRound();

        if (!targetRound) {
          setError('Nenhuma rodada ativa encontrada no momento.');
          return;
        }

        const sextetData = await roundService.getMySextet(targetRound.id);
        
        if (!sextetData) {
          navigate('/aluno');
          return;
        }

        setSextet(sextetData);
        setStaffList(formatInitialStaffList(targetRound.staff, sextetData.preferences));

      } catch (err) {
        setError(err.message || 'Não foi possível carregar as preferências.');
      } finally {
        setLoading(false);
      }
    };

    loadPreferences();
  }, [paramRoundId, navigate]);

  // Função auxiliar isolada para não poluir o fluxo principal
  const formatInitialStaffList = (staff, savedPreferences) => {
    if (!savedPreferences || savedPreferences.length === 0) return staff;
    return [...staff].sort((a, b) => 
      savedPreferences.indexOf(a.id) - savedPreferences.indexOf(b.id)
    );
  };

  const moveUp = (index) => {
    if (index === 0) return;
    const newList = [...staffList];
    [newList[index - 1], newList[index]] = [newList[index], newList[index - 1]];
    setStaffList(newList);
  };

  const moveDown = (index) => {
    if (index === staffList.length - 1) return;
    const newList = [...staffList];
    [newList[index + 1], newList[index]] = [newList[index], newList[index + 1]];
    setStaffList(newList);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      
      const payload = {
        staff_ids: staffList.map(staff => staff.id),
        expected_version: sextet.preference_version,
      };

      const responseData = await sextetService.updatePreferences(sextet.id, payload);
      
      setSextet(prev => ({ ...prev, preference_version: responseData.version }));
      navigate('/aluno');
      
    } catch (err) {
      if (err.code === 'PREFERENCE_VERSION_CONFLICT') {
         setError('As preferências foram alteradas em outra aba. Recarregue a página antes de salvar.');
      } else {
         setError(err.message || 'Erro ao salvar preferências.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Carregando preferências...</div>;

  const isLeader = sextet?.members?.[0]?.id === user.id;

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

      {error && (
        <Alert variant="error">
          {error}
        </Alert>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
        <div className="flex justify-between items-center p-4 border-b border-gray-200 bg-gray-50 text-sm font-medium text-gray-700">
          <span>{staffList.length} de {staffList.length} posicionados</span>
          <span>Versão {sextet?.preference_version}</span>
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