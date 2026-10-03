import { useCallback, useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';

function errorText(error) {
  return `${error.message || 'Não foi possível concluir a operação.'}${error.request_id ? ` Código: ${error.request_id}` : ''}`;
}

export default function AdminCadastros() {
  const [students, setStudents] = useState([]);
  const [staff, setStaff] = useState([]);
  const [studentForm, setStudentForm] = useState({ name: '', email: '', is_captain: false, phone: '' });
  const [staffForm, setStaffForm] = useState({ name: '', email: '' });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dispatch, setDispatch] = useState(null);
  const [access, setAccess] = useState(null);

  const refresh = useCallback(async () => {
    const [studentRows, staffRows] = await Promise.all([adminService.students(true), adminService.staff()]);
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
      await adminService.addStudent(studentForm.name.trim(), studentForm.email.trim(), studentForm.is_captain, studentForm.phone.trim());
      setStudentForm({ name: '', email: '', is_captain: false, phone: '' });
    }, 'Cadastro incluído. Apenas capitães recebem acesso.');
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

  async function restoreStudent(student) {
    await run(() => adminService.restoreStudent(student.id), 'Aluno restaurado. Gere um novo acesso ou envie as credenciais.');
  }

  async function issueAccess(student) {
    if (!window.confirm(`Gerar um novo acesso para ${student.name}? A senha anterior e as sessões atuais serão invalidadas. Você verá a nova senha uma única vez para entregar ao aluno.`)) return;
    setAccess(null);
    await run(async () => setAccess(await adminService.issueStudentAccess(student.id)), 'Acesso gerado para entrega manual.');
  }

  async function changeCaptain(student) {
    if (!window.confirm(`${student.is_captain ? 'Retirar' : 'Definir'} a função de capitão de ${student.name}? O acesso atual será invalidado. Alterações em grupos ativos exigem arquivar a rodada.`)) return;
    await run(() => adminService.setCaptain(student.id, !student.is_captain), 'Função atualizada. Gere novas credenciais se este aluno for capitão.');
  }

  async function removeStaff(person) {
    if (!window.confirm(`Remover ${person.name} da lista de servidores ativos?`)) return;
    await run(() => adminService.removeStaff(person.id), 'Servidor removido.');
  }

  async function sendCredentials() {
    const pending = students.filter((student) => !student.removed_at && student.is_captain && !student.credentials_issued).length;
    if (!pending) return;
    if (!window.confirm(`Enviar login e senha por e-mail aos ${pending} capitães pendentes? Essa ação envia mensagens reais e não deve ser repetida para quem já recebeu.`)) return;
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

  const currentStudents = students.filter((student) => !student.removed_at);
  const pending = currentStudents.filter((student) => student.is_captain && !student.credentials_issued).length;
  const activeStaff = staff.filter((person) => person.active !== false);

  return (
    <div className="app-page">
      <div className="app-page-head"><div>
        <p className="app-eyebrow">Administração · participantes</p><h1 className="app-title">Cadastros e credenciais</h1>
        <p className="app-subtitle">Identifique os capitães que acessam o sistema. Os demais alunos ficam disponíveis apenas para compor os grupos.</p>
      </div><span className="app-pill neutral">{currentStudents.length} alunos</span>
      </div>
      {error && <div role="alert" className="p-3 rounded bg-red-50 text-red-800 border border-red-200">{error}</div>}
      {notice && <div role="status" className="p-3 rounded bg-green-50 text-green-800 border border-green-200">{notice}</div>}
      {access && <section className="app-card app-card-pad space-y-2" aria-label="Acesso gerado"><h2 className="font-semibold">Acesso para entrega manual</h2><p className="text-sm">Copie os dados antes de fechar. A senha não poderá ser consultada novamente.</p><p className="break-all text-sm">Login: <code>{access.login}</code></p><p className="break-all text-sm">Senha: <code>{access.password}</code></p><button type="button" className="app-button secondary" onClick={() => setAccess(null)}>Fechar acesso</button></section>}
      {loading ? <p>Carregando cadastros...</p> : <>
        <section className="app-card app-card-pad space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Alunos ({currentStudents.length})</h2>
              <p className="text-sm text-gray-600">{currentStudents.filter((student) => student.is_captain).length} capitães; {pending} aguardando credenciais. Os demais integrantes não têm acesso.</p>
            </div>
            <button type="button" disabled={busy || pending === 0} onClick={sendCredentials} className="app-button">{busy ? 'Aguarde...' : `Enviar credenciais (${pending})`}</button>
          </div>
          {dispatch && <div role="status" className="p-3 rounded bg-blue-50 text-blue-900 text-sm">
            Lote: {dispatch.sent} enviados; {dispatch.pending_remaining} ainda pendentes. {dispatch.failed.length > 0 && `${dispatch.failed.length} falhas. Revise os endereços e tente novamente somente para os pendentes.`}
            {dispatch.failed.length > 0 && <ul className="mt-2 list-disc pl-5">{dispatch.failed.map((failure) => <li key={failure.email}>{failure.email}: {failure.code}</li>)}</ul>}
          </div>}
          <form onSubmit={addStudent} className="flex flex-wrap gap-2">
            <input aria-label="Nome do aluno" required minLength={2} maxLength={160} placeholder="Nome do aluno" value={studentForm.name} onChange={(e) => setStudentForm({ ...studentForm, name: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <input aria-label="E-mail do aluno" type="email" required placeholder="E-mail do aluno" value={studentForm.email} onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <input aria-label="Telefone do aluno" type="tel" maxLength={32} placeholder="Telefone (opcional)" value={studentForm.phone} onChange={(e) => setStudentForm({ ...studentForm, phone: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={studentForm.is_captain} onChange={(e) => setStudentForm({ ...studentForm, is_captain: e.target.checked })} />Capitão com acesso ao sistema</label>
            <button disabled={busy} className="app-button secondary">Adicionar aluno</button>
          </form>
          <div className="max-h-80 overflow-auto border rounded app-data-table">
            <table className="w-full text-sm"><thead className="bg-gray-50"><tr><th className="text-left p-2">Nome</th><th className="text-left p-2">E-mail</th><th className="text-left p-2">Telefone</th><th className="text-left p-2">Situação</th><th className="p-2">Ação</th></tr></thead>
              <tbody>{students.map((student) => <tr key={student.id} className="border-t"><td data-label="Nome" className="p-2">{student.name}</td><td data-label="E-mail" className="p-2">{student.email}</td><td data-label="Telefone" className="p-2">{student.phone || 'Não informado'}</td><td data-label="Situação" className="p-2">{student.removed_at ? 'Removido' : student.is_captain ? (student.active ? 'Capitão · acesso ativo' : 'Capitão · acesso pendente') : 'Integrante · sem acesso'}</td><td data-label="Ação" className="p-2 text-right"><div className="flex flex-wrap justify-end gap-3">{student.removed_at ? <button type="button" disabled={busy} onClick={() => restoreStudent(student)} className="text-green-700 disabled:opacity-50">Restaurar</button> : <>{student.is_captain && <button type="button" disabled={busy} onClick={() => issueAccess(student)} className="text-green-700 disabled:opacity-50">Gerar acesso</button>}<button type="button" disabled={busy} onClick={() => changeCaptain(student)} className="text-green-700 disabled:opacity-50">{student.is_captain ? 'Tornar integrante' : 'Definir capitão'}</button><button type="button" disabled={busy} onClick={() => removeStudent(student)} className="text-red-700 disabled:opacity-50">Remover</button></>}</div></td></tr>)}</tbody>
            </table>
          </div>
        </section>
        <section className="app-card app-card-pad space-y-4">
          <h2 className="text-lg font-semibold">Servidores ativos ({activeStaff.length})</h2>
          <form onSubmit={addStaff} className="flex flex-wrap gap-2">
            <input aria-label="Nome do servidor" required minLength={2} maxLength={160} placeholder="Nome do servidor" value={staffForm.name} onChange={(e) => setStaffForm({ ...staffForm, name: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <input aria-label="E-mail do servidor" type="email" placeholder="E-mail do servidor (opcional)" value={staffForm.email} onChange={(e) => setStaffForm({ ...staffForm, email: e.target.value })} className="border rounded px-3 py-2 flex-1 min-w-48" />
            <button disabled={busy} className="app-button secondary">Adicionar servidor</button>
          </form>
          <div className="max-h-80 overflow-auto border rounded app-data-table">
            <table className="w-full text-sm"><thead className="bg-gray-50"><tr><th className="text-left p-2">Nome</th><th className="text-left p-2">E-mail</th><th className="p-2">Ação</th></tr></thead>
              <tbody>{activeStaff.map((person) => <tr key={person.id} className="border-t"><td data-label="Nome" className="p-2">{person.name}</td><td data-label="E-mail" className="p-2">{person.email}</td><td data-label="Ação" className="p-2 text-right"><button type="button" disabled={busy} onClick={() => removeStaff(person)} className="text-red-700 disabled:opacity-50">Remover</button></td></tr>)}</tbody>
            </table>
          </div>
        </section>
      </>}
    </div>
  );
}
