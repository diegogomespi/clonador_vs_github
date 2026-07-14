import html
import shutil
import os
import subprocess
import sys
import time
import io
import contextlib

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
    if message is None:
        return
    text = str(message).replace("\r\n", "\n").replace("\r", "\n")
    for line in text.split("\n"):
        line = line.rstrip()
        if not line:
            continue
        INSTALL_LOGS.append(line)
    if len(INSTALL_LOGS) > 200:
        del INSTALL_LOGS[:-200]


def render_loading(stage, detail="", progress=0, error=None):
    safe_logs = "<br>".join(html.escape(line) for line in INSTALL_LOGS[-24:])
    full_log_text = "\n".join(INSTALL_LOGS)
    safe_log_value = html.escape(full_log_text, quote=True)
    safe_stage = html.escape(stage)
    safe_detail = html.escape(error) if error else html.escape(detail)
    color = "#ef4444" if error else "#8b5cf6"
    progress = max(0, min(100, int(progress)))
    step_cards = "".join(
        f"""
        <div style='padding:12px 14px; border-radius:14px; background:linear-gradient(180deg, #171125 0%, #120d1e 100%); border:1px solid #2b1d47; color:#d8c8f5; font-size:13px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);'>
          <div style='opacity:0.92; margin-bottom:6px;'>{html.escape(name)}</div>
          <strong style='color:white; font-size:18px; letter-spacing:0.02em;'>{pct}%</strong>
        </div>
        """
        for name, pct in INSTALL_STEPS
    )
    return f"""
<div style='background: radial-gradient(circle at top, #130d22 0%, #09070f 58%); padding: 34px; border-radius: 22px; text-align: center; font-family: Inter, sans-serif; max-width: 920px; margin: 0 auto; border: 1px solid #221535; box-shadow: 0 24px 60px rgba(0,0,0,0.45); position:relative; overflow:hidden;'>
  <div style='position:absolute; inset:-120px auto auto -80px; width:220px; height:220px; background:rgba(139,92,246,0.10); filter:blur(40px); border-radius:50%;'></div>
  <div style='position:absolute; inset:auto -60px -80px auto; width:220px; height:220px; background:rgba(99,102,241,0.08); filter:blur(42px); border-radius:50%;'></div>
  <div style='position:relative; display:flex; align-items:center; justify-content:center; gap:12px; margin-bottom: 8px;'>
    <div style='width:18px; height:18px; border-radius:50%; background:{color}; box-shadow:0 0 20px {color};'></div>
    <h2 style='color: white; margin: 0; font-size: 2.1em; font-weight: 700; letter-spacing:-0.02em;'>Clonador VS Studio</h2>
  </div>
  <p style='color: #b9a3dd; margin: 0 0 18px 0; font-size: 15px;'>By Diego Gomes</p>
  <div style='position:relative; background:#130d1f; border:1px solid #2b1d47; border-radius:999px; overflow:hidden; height:18px; margin: 0 auto 18px auto; max-width: 700px; box-shadow: inset 0 1px 4px rgba(0,0,0,0.35);'>
    <div style='height:100%; width:{progress}%; background:linear-gradient(90deg, #6d28d9 0%, #a78bfa 100%); transition: width 0.3s ease;'></div>
  </div>
  <div style='position:relative; color:#f3edff; font-size: 2em; font-weight: 700; margin-bottom: 8px; letter-spacing:-0.02em;'>{safe_stage}</div>
  <div style='position:relative; color:#a78bfa; font-size: 15px; margin-bottom: 20px; min-height: 20px;'>{safe_detail}</div>
  <div style='display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 0 auto 20px auto; max-width: 760px; position:relative;'>
    {step_cards}
  </div>
  <div style='display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:10px; position:relative;'>
    <div style='color:#e9ddff; font-size:15px; font-weight:600;'>Log completo da instalacao</div>
    <button onclick="navigator.clipboard.writeText(document.getElementById('codex-full-log').value)" style='background:linear-gradient(180deg, #221535 0%, #171024 100%); color:#ffffff; border:1px solid #3a2460; border-radius:10px; padding:9px 14px; cursor:pointer; font-weight:600;'>Copiar log</button>
  </div>
  <div style='text-align:left; background:#05030a; border:1px solid #221535; color:#d1c4eb; padding:16px; border-radius:16px; min-height:230px; max-height:340px; overflow:auto; font-family: Consolas, monospace; font-size: 12px; line-height: 1.55; box-shadow: inset 0 1px 0 rgba(255,255,255,0.03); position:relative;'>
    {safe_logs or 'Aguardando inicio da instalacao...'}
  </div>
  <textarea id='codex-full-log' style='position:absolute; left:-9999px; top:-9999px;'>{safe_log_value}</textarea>
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
    log_stream = io.StringIO()
    with contextlib.redirect_stdout(log_stream), contextlib.redirect_stderr(log_stream):
        gdown.download_folder(url=public_url, output=download_root, quiet=False, use_cookies=False)
    append_log(log_stream.getvalue())

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
    enable_asr=True,
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
        local_asr_dir = "/content/models/ASR/whisper-large-v3-turbo"
        if not os.path.isfile(os.path.join(local_asr_dir, "config.json")):
            append_log("ASR local nao encontrado no pacote publico. O sistema usara o modo sem ASR local.")
            local_asr_dir = ""
        else:
            append_log("OK: ASR local encontrado no pacote publico")
        final_enable_asr = bool(enable_asr and local_asr_dir)

        update_loading("Carregando aplicacao", "Importando arquivos do projeto...", 75)
        append_log("> Importando app.py e config.py...")
        os.environ["HF_TOKEN"] = hf_token.strip()
        os.environ["ENABLE_ASR"] = "true" if final_enable_asr else "false"
        os.environ["MODEL_PUBLIC_URL"] = model_public_url.strip()
        os.environ["MODEL_LOCAL_PATH"] = local_model_dir.strip() if local_model_dir else ""
        os.environ["ASR_MODEL_LOCAL_PATH"] = local_asr_dir.strip() if local_asr_dir else ""
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
