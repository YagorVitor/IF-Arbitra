# Frontend IF-Arbitra

Aplicação React/Vite para alunos e administradores. A API de produção é servida pelo proxy em `vercel.json`, sob `/api`, para manter o cookie de sessão na origem do site.

## Desenvolvimento local

```bash
npm ci
npm run dev
```

Copie `.env.example` para `.env.local` quando quiser acessar um backend local em `http://localhost:8000`. Nesse caso, configure `FRONTEND_URL=http://localhost:5173` no backend. Não defina `VITE_API_URL` na Vercel; em produção as requisições devem usar `/api`.

## Publicação na Vercel

- Repositório: `YagorVitor/IF-Arbitra`, branch `frontend`.
- Root Directory: `frontend`.
- Framework Preset: Vite.
- Build Command: `npm run build`.
- Output Directory: `dist`.
- Mantenha o arquivo `vercel.json` no diretório `frontend`.
- Use uma URL de produção estável da Vercel. Previews com outras origens não passam na verificação de `Origin` do backend.

Após obter a URL HTTPS de produção, configure no serviço Railway `IF-Arbitra`:

```text
FRONTEND_URL=https://URL-EXATA-DA-VERCEL
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
```

O envio de credenciais só funcionará após configurar SMTP no Railway. A conta administradora deve ser criada pela CLI do backend; ela não é criada pelo frontend. Antes do evento, confira o login de administrador, o cadastro, a rodada e o envio de teste para um endereço seu.
