import { useCallback, useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';

function errorText(error) {
  return `${error.message || 'Não foi possível concluir a operação.'}${error.request_id ? ` Código: ${error.request_id}` : ''}`;
}

export default function AdminCadastros() {
  const [students, setStudents] = useState([]);
  const [staff, setStaff] = useState([]);
  const [studentForm, setStudentForm] = useState({ name: '', email: '' });
  const [staffForm, setStaffForm] = useState({ name: '', email: '' });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dispatch, setDispatch] = useState(null);

  const refresh = useCallback(async () => {
    const [studentRows, staffRows] = await Promise.all([adminService.students(), adminService.staff()]);
    setStudents(studentRows);
    setStaff(staffRows);
  }, []);

  useEffect(() => {
    refresh().catch((err) => setError(errorText(err))).finally(() => setLoading(false));
  }, [refresh]);

  async function run(action, success) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
      await refresh();
      setNotice(success);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function addStudent(event) {
    event.preventDefault();
    await run(async () => {
      await adminService.addStudent(studentForm.name.trim(), studentForm.email.trim());
      setStudentForm({ name: '', email: '' });
    }, 'Aluno incluído como pendente de credenciais.');
  }

  async function addStaff(event) {
    event.preventDefault();
    await run(async () => {
      await adminService.addStaff(staffForm.name.trim(), staffForm.email.trim());
      setStaffForm({ name: '', email: '' });
    }, 'Servidor incluído.');
  }

  async function removeStudent(student) {
    if (!window.confirm(`Remover ${student.name} do cadastro?`)) return;
    await run(() => adminService.removeStudent(student.id), 'Aluno removido.');
  }

  async function removeStaff(person) {
    if (!window.confirm(`Remover ${person.name} da lista de servidores ativos?`)) return;
    await run(() => adminService.removeStaff(person.id), 'Servidor removido.');
  }

  async function sendCredentials() {
    const pending = students.filter((student) => !student.credentials_issued).length;
    if (!pending) return;
    if (!window.confirm(`Enviar login e senha por e-mail aos ${pending} alunos pendentes? Essa ação envia mensagens reais e não deve ser repetida para quem já recebeu.`)) return;
    setBusy(true);
    setError('');
    setNotice('');
    setDispatch(null);
    try {
      const result = await adminService.dispatchCredentials();
      setDispatch(result);
      await refresh();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const pending = students.filter((student) => !student.credentials_issued).length;
  const activeStaff = staff.filter((person) => person.active !== false);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Cadastros e credenciais</h1>
        <p className="text-sm text-gray-600 mt-1">Os cadastros iniciais já estão no sistema. Inclua ou remova exceções antes de enviar as credenciais.</p>
      </div>
      {error && <div role="alert" className="p-3 rounded bg-red-50 text-red-800 border border-red-200">{error}</div>}
      {notice && <div role="status" className="p-3 rounded bg-green-50 text-green-800 border border-green-200">{notice}</div>}
      {loading ? <p>Carregando cadastros...</p> : <>
        <section className="border rounded-lg p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Alunos ({students.length})</h2>
              <p className="text-sm text-gray-600">{pending} pendentes de credenciais; {students.length - pending} já receberam.</p>
            </div>
            <button type="button" disabled={busy || pending === 0} onClick={sendCredentials} className="px-4 py-2 rounded bg-[#0A3D2A] text-white disabled:opacity-50">{busy ? 'Aguarde...' : `Enviar credenciais (${pending})`}</button>
          </div>
          {dispatch && <div role="status" className="p-3 rounded bg-blue-50 text-blue-900 text-sm">
            Lote: {dispatch.sent} enviados; {dispatch.pending_remaining} ainda pendentes. {dispatch.failed.length > 0 && `${dispatch.failed.length} falhas. Revise os endereços e tente novamente somente para os pendentes.`}
            {dispatch.failed.length > 0 && <ul className="mt-2 list-disc pl-5">{dispatch.failed.map((failure) => <li key={failure.email}>{failure.email}: {failure.code}</li>)}</ul>}
          </div>}
          <form onSubmit={addStudent} className="flex flex-wrap gap-2">
            <input aria-label="Nome do aluno" required minLength={2} maxLength={160} placeholder="Nome do aluno" value={studentForm.name} onChange={(e) => setStudentForm({ ...studentForm, name: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <input aria-label="E-mail do aluno" type="email" required placeholder="E-mail do aluno" value={studentForm.email} onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <button disabled={busy} className="px-4 py-2 border rounded disabled:opacity-50">Adicionar aluno</button>
          </form>
          <div className="max-h-80 overflow-auto border rounded">
            <table className="w-full text-sm"><thead className="bg-gray-50"><tr><th className="text-left p-2">Nome</th><th className="text-left p-2">E-mail</th><th className="text-left p-2">Situação</th><th className="p-2">Ação</th></tr></thead>
              <tbody>{students.map((student) => <tr key={student.id} className="border-t"><td className="p-2">{student.name}</td><td className="p-2">{student.email}</td><td className="p-2">{student.credentials_issued ? 'Credenciais enviadas' : 'Pendente'}</td><td className="p-2 text-right"><button type="button" disabled={busy} onClick={() => removeStudent(student)} className="text-red-700 disabled:opacity-50">Remover</button></td></tr>)}</tbody>
            </table>
          </div>
        </section>
        <section className="border rounded-lg p-5 space-y-4">
          <h2 className="text-lg font-semibold">Servidores ativos ({activeStaff.length})</h2>
          <form onSubmit={addStaff} className="flex flex-wrap gap-2">
            <input aria-label="Nome do servidor" required minLength={2} maxLength={160} placeholder="Nome do servidor" value={staffForm.name} onChange={(e) => setStaffForm({ ...staffForm, name: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <input aria-label="E-mail do servidor" type="email" required placeholder="E-mail do servidor" value={staffForm.email} onChange={(e) => setStaffForm({ ...staffForm, email: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <button disabled={busy} className="px-4 py-2 border rounded disabled:opacity-50">Adicionar servidor</button>
          </form>
          <div className="max-h-80 overflow-auto border rounded">
            <table className="w-full text-sm"><thead className="bg-gray-50"><tr><th className="text-left p-2">Nome</th><th className="text-left p-2">E-mail</th><th className="p-2">Ação</th></tr></thead>
              <tbody>{activeStaff.map((person) => <tr key={person.id} className="border-t"><td className="p-2">{person.name}</td><td className="p-2">{person.email}</td><td className="p-2 text-right"><button type="button" disabled={busy} onClick={() => removeStaff(person)} className="text-red-700 disabled:opacity-50">Remover</button></td></tr>)}</tbody>
            </table>
          </div>
        </section>
      </>}
    </div>
  );
}
