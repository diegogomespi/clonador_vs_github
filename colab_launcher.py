import html
import shutil
import os
import subprocess
import sys
import time

import IPython.display as display
from IPython.display import clear_output


INSTALL_STEPS = [
    ("Sincronizando GitHub", 10),
    ("Instalando dependencias", 45),
    ("Carregando aplicacao", 75),
    ("Baixando modelo", 90),
    ("Publicando interface", 97),
]

INSTALL_LOGS = []
DISPLAY_HANDLE = None


def append_log(message):
    INSTALL_LOGS.append(message)
    if len(INSTALL_LOGS) > 200:
        del INSTALL_LOGS[:-200]


def render_loading(stage, detail="", progress=0, error=None):
    safe_logs = "<br>".join(html.escape(line) for line in INSTALL_LOGS[-12:])
    safe_stage = html.escape(stage)
    safe_detail = html.escape(error) if error else html.escape(detail)
    color = "#ef4444" if error else "#8b5cf6"
    progress = max(0, min(100, int(progress)))
    return f"""
<div style='background: #0a0812; padding: 32px; border-radius: 16px; text-align: center; font-family: Inter, sans-serif; max-width: 820px; margin: 0 auto; border: 1px solid #1e1533; box-shadow: 0 18px 50px rgba(0,0,0,0.35);'>
  <div style='display:flex; align-items:center; justify-content:center; gap:12px; margin-bottom: 10px;'>
    <div style='width:18px; height:18px; border-radius:50%; background:{color}; box-shadow:0 0 18px {color};'></div>
    <h2 style='color: white; margin: 0; font-size: 1.8em; font-weight: 600;'>Clonador VS Studio</h2>
  </div>
  <p style='color: #b9a3dd; margin: 0 0 18px 0; font-size: 15px;'>By Diego Gomes</p>
  <div style='background:#130d1f; border:1px solid #2b1d47; border-radius:999px; overflow:hidden; height:16px; margin: 0 auto 16px auto; max-width: 620px;'>
    <div style='height:100%; width:{progress}%; background:linear-gradient(90deg, #6d28d9 0%, #a78bfa 100%); transition: width 0.3s ease;'></div>
  </div>
  <div style='color:#e9ddff; font-size: 24px; font-weight: 600; margin-bottom: 8px;'>{safe_stage}</div>
  <div style='color:#a78bfa; font-size: 14px; margin-bottom: 18px; min-height: 20px;'>{safe_detail}</div>
  <div style='display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 0 auto 18px auto; max-width: 720px;'>
    {''.join(f"<div style='padding:10px 12px; border-radius:12px; background:#130d1f; border:1px solid #24173c; color:#d8c8f5; font-size:13px;'>{html.escape(name)}<br><strong style='color:white;'>{pct}%</strong></div>" for name, pct in INSTALL_STEPS)}
  </div>
  <div style='text-align:left; background:#05030a; border:1px solid #221535; color:#d1c4eb; padding:16px; border-radius:12px; min-height:180px; max-height:260px; overflow:auto; font-family: Consolas, monospace; font-size: 12px; line-height: 1.5;'>
    {safe_logs or 'Aguardando inicio da instalacao...'}
  </div>
</div>
"""


def update_loading(stage, detail="", progress=0, error=None):
    global DISPLAY_HANDLE
    html_block = render_loading(stage, detail=detail, progress=progress, error=error)
    if DISPLAY_HANDLE is None:
        DISPLAY_HANDLE = display.display(display.HTML(html_block), display_id=True)
    else:
        DISPLAY_HANDLE.update(display.HTML(html_block))


def run_command(command, stage, detail, progress, workdir=None):
    update_loading(stage, detail, progress)
    append_log(f"> {detail}")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=workdir,
    )
    if process.stdout is not None:
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            append_log(line)
            update_loading(stage, detail, progress)
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"Falha na etapa: {stage} (codigo {return_code})")
    append_log(f"OK: {stage}")
    update_loading(stage, detail, progress)


def sync_repo(repo_url, branch, project_dir):
    repo_dir = os.path.abspath(project_dir)
    parent_dir = os.path.dirname(repo_dir)
    os.makedirs(parent_dir, exist_ok=True)

    if not os.path.exists(repo_dir):
        run_command(
            ["git", "clone", "--branch", branch, repo_url, repo_dir],
            "Sincronizando GitHub",
            "Clonando repositorio pela primeira vez...",
            10,
        )
    else:
        run_command(
            ["git", "fetch", "--all"],
            "Sincronizando GitHub",
            "Buscando atualizacoes no GitHub...",
            10,
            workdir=repo_dir,
        )
        run_command(
            ["git", "reset", "--hard", f"origin/{branch}"],
            "Sincronizando GitHub",
            "Aplicando a ultima versao do GitHub...",
            20,
            workdir=repo_dir,
        )

    return repo_dir


def install_requirements(project_dir):
    requirements_path = os.path.join(project_dir, "requirements.txt")
    run_command(
        [sys.executable, "-m", "pip", "install", "-r", requirements_path],
        "Instalando dependencias",
        "Instalando requirements.txt...",
        45,
        workdir=project_dir,
    )


def prepare_public_model(model_public_url, local_model_dir):
    public_url = (model_public_url or "").strip()
    if not public_url:
        return ""

    if os.path.isdir(local_model_dir):
        try:
            shutil.rmtree(local_model_dir)
        except OSError:
            pass

    os.makedirs(os.path.dirname(local_model_dir), exist_ok=True)
    append_log("> Baixando modelo publico do Google Drive...")
    update_loading("Baixando modelo", "Baixando modelo publico do Google Drive...", 88)

    import gdown

    download_root = os.path.dirname(local_model_dir)
    gdown.download_folder(url=public_url, output=download_root, quiet=False, use_cookies=False)

    config_path = os.path.join(local_model_dir, "config.json")
    model_weights = os.path.join(local_model_dir, "model.safetensors")
    if not (os.path.isfile(config_path) and os.path.isfile(model_weights)):
        append_log("Modelo publico baixado, mas parece incompleto. Faltam arquivos principais.")
        return ""

    append_log("OK: modelo baixado do Google Drive")
    return local_model_dir


def show_success(share_url):
    clear_output(wait=True)
    html_btn = f"""
    <div style='background: #0a0812; padding: 40px; border-radius: 12px; text-align: center; font-family: Inter, sans-serif; max-width: 650px; margin: 0 auto; border: 1px solid #1e1533;'>
      <h2 style='color: white; margin: 0 0 10px 0; font-size: 1.8em; font-weight: 500;'>Sistema Online!</h2>
      <p style='color: #b9a3dd; font-size: 15px; margin: 0 0 20px 0;'>Clonador VS Studio - By Diego Gomes</p>
      <a href='{share_url}' target='_blank' style='background: #7b6196; color: #ffffff; padding: 15px 35px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 16px; display: inline-block; margin-top: 15px; transition: opacity 0.2s;'>
        ABRIR GERADOR (NOVA ABA)
      </a>
      <p style='color: #444; font-size: 0.8em; margin: 25px 0 0 0;'>Celula em execucao. Nao feche ou pause o Colab.</p>
    </div>
    """
    display.display(display.HTML(html_btn))


def run_from_colab(
    repo_url,
    branch="main",
    project_dir="/content/clonador_vs_github",
    model_public_url="",
    hf_token="",
    telegram_bot_token="",
    telegram_chat_id="",
    telegram_send_audio=True,
    telegram_silent=False,
    telegram_proxy_url="",
    telegram_proxy_secret="",
):
    try:
        update_loading("Preparando ambiente", "Iniciando configuracao do Colab...", 5)
        repo_dir = sync_repo(repo_url, branch, project_dir)
        install_requirements(repo_dir)
        local_model_dir = prepare_public_model(model_public_url, "/content/models/OmniVoice")

        update_loading("Carregando aplicacao", "Importando arquivos do projeto...", 75)
        append_log("> Importando app.py e config.py...")
        os.environ["HF_TOKEN"] = hf_token.strip()
        os.environ["MODEL_PUBLIC_URL"] = model_public_url.strip()
        os.environ["MODEL_LOCAL_PATH"] = local_model_dir.strip() if local_model_dir else ""
        os.environ["TELEGRAM_BOT_TOKEN"] = telegram_bot_token.strip()
        os.environ["TELEGRAM_CHAT_ID"] = telegram_chat_id.strip()
        os.environ["TELEGRAM_SEND_AUDIO"] = "true" if telegram_send_audio else "false"
        os.environ["TELEGRAM_SILENT"] = "true" if telegram_silent else "false"
        os.environ["TELEGRAM_PROXY_URL"] = telegram_proxy_url.strip()
        os.environ["TELEGRAM_PROXY_SECRET"] = telegram_proxy_secret.strip()
        if repo_dir not in sys.path:
            sys.path.insert(0, repo_dir)

        import importlib

        app = importlib.import_module("app")
        app = importlib.reload(app)

        def model_status(stage, detail, progress):
            append_log(detail)
            update_loading(stage, detail, progress)

        app.load_model(status_callback=model_status)
        append_log("OK: modelo carregado")

        update_loading("Publicando interface", "Subindo interface Gradio...", 97)
        _, _, share_url = app.create_app().queue().launch(share=True, inline=False, quiet=True)
        append_log("OK: interface publicada com sucesso")

        show_success(share_url)
        while True:
            time.sleep(1)
    except Exception as exc:
        append_log(str(exc))
        update_loading("Erro ao carregar", "Revise o log abaixo para descobrir a etapa que falhou.", 100, error=str(exc))
        raise
