# Cloudflare Worker Setup

## O que voce precisa

1. Conta Cloudflare.
2. Um Worker novo conectado ao GitHub ou deploy com Wrangler.
3. Secrets no Worker:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `WORKER_SHARED_SECRET` opcional

## Estrutura pronta neste repo

- `cloudflare-worker/src/index.js`: Worker que recebe o mp3 e encaminha ao Telegram
- `cloudflare-worker/wrangler.jsonc`: configuracao do Worker
- `cloudflare-worker/.dev.vars.example`: exemplo de secrets locais

## Jeito mais simples

1. Entre na pasta `cloudflare-worker`
2. Rode:

```bash
npm install
npx wrangler login
npx wrangler secret put TELEGRAM_BOT_TOKEN
npx wrangler secret put TELEGRAM_CHAT_ID
```

Opcional para proteger a URL:

```bash
npx wrangler secret put WORKER_SHARED_SECRET
```

3. Faça o deploy:

```bash
npx wrangler deploy
```

4. Copie a URL publicada do Worker, algo como:

```text
https://clonador-vs-telegram-worker.<sua-subconta>.workers.dev
```

5. No notebook `clonador_vs_studio_colab.ipynb`, preencha:

```python
TELEGRAM_PROXY_URL = "https://sua-url-do-worker"
TELEGRAM_PROXY_SECRET = ""
```

Se tiver criado `WORKER_SHARED_SECRET`, coloque o mesmo valor em `TELEGRAM_PROXY_SECRET`.

## Fluxo final

- GitHub -> Colab: atualiza o codigo
- GitHub -> Cloudflare: atualiza o Worker
- Colab -> Worker: envia o mp3
- Worker -> Telegram: usa o token escondido em secret
