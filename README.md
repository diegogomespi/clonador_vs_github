# Clonador VS Studio

Projeto preparado para rodar pelo Google Colab sempre puxando a ultima versao do GitHub.

## Estrutura

- `app.py`: interface Gradio e logica principal do gerador/clonador
- `config.py`: nome do sistema, Telegram e opcoes centrais
- `requirements.txt`: dependencias instaladas no Colab
- `colab_launcher.py`: sincroniza o repo, instala dependencias e sobe o app
- `clonador_vs_studio_colab.ipynb`: notebook que o usuario abre no Colab

## Como usar com GitHub

1. Crie um repositorio GitHub para esta pasta.
2. Envie todos os arquivos desta pasta para o repositorio.
3. Edite a primeira celula de `clonador_vs_studio_colab.ipynb` e troque `REPO_URL` pela URL real do seu repositorio.
4. Abra o notebook no Google Colab.
5. Rode a celula principal. Ela vai:
   - clonar ou atualizar o repo
   - instalar `requirements.txt`
   - carregar o modelo
   - publicar a interface

## Atualizacoes

Depois que os outros computadores estiverem usando o notebook pelo GitHub, basta atualizar o repo. Na proxima execucao, o Colab vai puxar a ultima versao.

## Observacoes

- O token do Telegram esta em `config.py`. Se o repositorio ficar publico, troque esse token antes.
- O envio para o Telegram esta habilitado e usa notificacao normal.
- A conversao para `mp3` depende de `ffmpeg`, que normalmente ja existe no Colab.
