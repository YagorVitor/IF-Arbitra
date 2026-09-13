import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../api/api';
import { useAuth } from '../../contexts/AuthContext';
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
    const fetchPreferencesData = async () => {
      try {
        setLoading(true);
        let targetRoundId = paramRoundId;

        // Se a rota não contiver roundId, descobre a rodada aberta atual
        if (!targetRoundId) {
          const rounds = await api.get('/api/rounds');
          const activeRound = rounds.find(r => r.status === 'OPEN' || r.preferences_open) || rounds[0];
          
          if (!activeRound) {
            setError('Nenhuma rodada ativa encontrada no momento.');
            return;
          }
          targetRoundId = activeRound.id;
        }

        const roundData = await api.get(`/api/rounds/${targetRoundId}`);
        const sextetData = await api.get(`/api/rounds/${targetRoundId}/my-sextet`);
        
        if (!sextetData) {
          navigate('/aluno');
          return;
        }

        setSextet(sextetData);

        if (sextetData.preferences && sextetData.preferences.length > 0) {
          const sortedStaff = [...roundData.staff].sort((a, b) => {
            return sextetData.preferences.indexOf(a.id) - sextetData.preferences.indexOf(b.id);
          });
          setStaffList(sortedStaff);
        } else {
          setStaffList(roundData.staff);
        }
      } catch (err) {
        setError(err.message || 'Não foi possível carregar as preferências.');
      } finally {
        setLoading(false);
      }
    };

    fetchPreferencesData();
  }, [paramRoundId, navigate]);

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

      const responseData = await api.put(`/api/sextets/${sextet.id}/preferences`, payload);
      
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