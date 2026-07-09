import os
import tempfile
import time
import wave

import gradio as gr
import numpy as np
import requests
import torch
from omnivoice import OmniVoice, OmniVoiceGenerationConfig
from pydub import AudioSegment

import config


LANGUAGES = [
    "Auto",
    "English (en)",
    "Chinese (zh)",
    "Japanese (ja)",
    "Korean (ko)",
    "French (fr)",
    "German (de)",
    "Spanish (es)",
    "Portuguese (pt)",
    "Russian (ru)",
    "Arabic (ar)",
    "Hindi (hi)",
    "Italian (it)",
    "Dutch (nl)",
    "Turkish (tr)",
    "Polish (pl)",
    "Swedish (sv)",
    "Thai (th)",
    "Vietnamese (vi)",
    "Indonesian (id)",
    "Malay (ms)",
]

CATEGORIES = {
    "Gender": ["male", "female"],
    "Age": ["child", "teenager", "young adult", "middle-aged", "elderly"],
    "Pitch": ["very low pitch", "low pitch", "moderate pitch", "high pitch", "very high pitch"],
    "Style": ["whisper"],
    "English Accent": [
        "american accent",
        "british accent",
        "australian accent",
        "canadian accent",
        "indian accent",
        "chinese accent",
        "japanese accent",
        "korean accent",
        "portuguese accent",
        "russian accent",
    ],
    "Chinese Dialect": [
        "Sichuan",
        "Shaanxi",
        "Guangdong",
        "Dongbei",
        "Henan",
        "Yunnan",
        "Guizhou",
        "Guilin",
        "Jinan",
    ],
}

ATTR_INFO = {
    "Gender": "Speaker gender",
    "Age": "Approximate speaker age",
    "Pitch": "Voice pitch level",
    "Style": "Speaking style",
    "English Accent": "English accent (effective for English text)",
    "Chinese Dialect": "Chinese dialect (effective for Chinese text)",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
* { font-family: 'Inter', sans-serif !important; }

body, .gradio-container {
    background-color: #0b0811 !important;
    background-image: radial-gradient(circle at 50% 0%, #1e1533 0%, #0b0811 50%) !important;
    color: #ffffff !important;
}

.gradio-container .form { background: transparent !important; border: none !important; box-shadow: none !important; }
.label-wrap { display: none !important; }

#caixa-texto {
    position: relative;
    background: #15121e !important;
    border-radius: 12px !important;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
    height: 100% !important;
}
#caixa-texto::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: linear-gradient(90deg, #4b6cb7 0%, #8b5cf6 100%);
    z-index: 10;
}
#caixa-texto textarea {
    background: transparent !important;
    border: none !important;
    color: #d1d5db !important;
    font-size: 16px !important;
    padding: 30px 25px !important;
    resize: none !important;
    box-shadow: none !important;
    min-height: 250px !important;
}
#caixa-texto textarea:focus { outline: none !important; border: none !important; }

#coluna-direita {
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    height: 100% !important;
}

#caixa-audio { border: none !important; background: transparent !important; margin-bottom: 10px !important; }
#caixa-audio .upload-container {
    background: #0f0a17 !important;
    border: 1px solid #3c2a5c !important;
    border-radius: 4px !important;
    min-height: 55px !important;
    height: 55px !important;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}
#caixa-audio .upload-container:hover { background: #1a1229 !important; }

#caixa-linguagem .wrap {
    background: #0f0a17 !important;
    border: 1px solid #201533 !important;
    border-radius: 4px !important;
    color: #d1d5db !important;
}

#botao-gerar {
    background: #0f0a17 !important;
    border: 1px solid #201533 !important;
    border-radius: 4px !important;
    color: #d1d5db !important;
    font-weight: 400 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 15px !important;
    box-shadow: none !important;
    transition: all 0.2s;
    margin-top: 15px !important;
    width: 100% !important;
}
#botao-gerar:hover { background: #1a1229 !important; border-color: #3c2a5c !important; }

#botao-gerar:disabled, button.primary:disabled {
    background: #1e1533 !important;
    border-color: #3c2a5c !important;
    color: #8b5cf6 !important;
    cursor: not-allowed !important;
    opacity: 0.8;
}

#caixa-resultado, #design-resultado { margin-top: 20px !important; }
#caixa-resultado .wrap, #caixa-resultado audio, #design-resultado .wrap, #design-resultado audio {
    background: #7b6196 !important;
    border-radius: 40px !important;
    border: none !important;
    padding: 5px 10px !important;
}
#caixa-resultado *, #design-resultado * { color: white !important; }
#telegram-clone-trigger, #telegram-design-trigger {
    display: none !important;
}
"""

HEAD = """
<script>
(() => {
  function bindDownloadLink(containerId, triggerId) {
    const container = document.getElementById(containerId);
    const triggerRoot = document.getElementById(triggerId);
    if (!container || !triggerRoot) return;
    const link = container.querySelector("a.download-link");
    if (!link || link.dataset.telegramBound === "1") return;

    link.dataset.telegramBound = "1";
    link.addEventListener("click", () => {
      const triggerButton = triggerRoot.tagName === "BUTTON" ? triggerRoot : triggerRoot.querySelector("button");
      if (triggerButton) {
        triggerButton.click();
      }
    }, true);
  }

  function attachWhenReady() {
    bindDownloadLink("caixa-resultado", "telegram-clone-trigger");
    bindDownloadLink("design-resultado", "telegram-design-trigger");
  }

  const observer = new MutationObserver(() => attachWhenReady());
  observer.observe(document.documentElement, { childList: true, subtree: true });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachWhenReady);
  } else {
    attachWhenReady();
  }
})();
</script>
"""

BRAND_HTML = f"""
<div style="text-align: center; margin-bottom: 30px; margin-top: 20px;">
    <h1 style="color: white; margin: 0; font-size: 30px; font-weight: 600;">{config.APP_TITLE}</h1>
    <p style="color: #6d4b99; font-size: 15px; font-weight: 400; margin: 8px 0 0 0;">By {config.APP_AUTHOR}</p>
</div>
"""

MODEL = None
SAMPLING_RATE = None


def telegram_enabled():
    return bool(
        config.TELEGRAM_SEND_AUDIO
        and config.TELEGRAM_BOT_TOKEN.strip()
        and config.TELEGRAM_CHAT_ID.strip()
    )


def telegram_proxy_enabled():
    return bool(config.TELEGRAM_SEND_AUDIO and config.TELEGRAM_PROXY_URL.strip())


def build_output_filename(prefix, extension="wav"):
    return f"Off_VS.{extension}"


def save_audio_tuple_to_wav(audio_tuple):
    sample_rate, waveform = audio_tuple
    channels = 1 if len(waveform.shape) == 1 else waveform.shape[1]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        temp_path = tmp_file.name
    with wave.open(temp_path, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(int(sample_rate))
        wav_file.writeframes(waveform.tobytes())
    return temp_path


def convert_wav_to_mp3(wav_path, caption="audio"):
    mp3_name = build_output_filename(caption, extension="mp3")
    mp3_path = os.path.join(tempfile.gettempdir(), mp3_name)
    audio_segment = AudioSegment.from_wav(wav_path)
    audio_segment.export(mp3_path, format="mp3", bitrate="192k")
    return mp3_path


def cleanup_old_audio_files(max_age_seconds=6 * 60 * 60):
    temp_dir = tempfile.gettempdir()
    now = time.time()
    for entry in os.listdir(temp_dir):
        if not (entry.startswith("Off_VS") or entry.startswith("clonador-vs-studio-")):
            continue
        full_path = os.path.join(temp_dir, entry)
        if not os.path.isfile(full_path):
            continue
        try:
            if now - os.path.getmtime(full_path) > max_age_seconds:
                os.remove(full_path)
        except OSError:
            pass


def send_audio_to_telegram(file_path, caption=""):
    if not telegram_enabled():
        return

    with open(file_path, "rb") as audio_file:
        file_name = os.path.basename(file_path)
        response = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendAudio",
            data={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "caption": (caption or f"Audio gerado pelo {config.APP_TITLE}")[:1024],
                "disable_notification": "true" if config.TELEGRAM_SILENT else "false",
                "title": config.APP_TITLE,
                "performer": config.APP_AUTHOR,
            },
            files={"audio": (file_name, audio_file, "audio/mpeg")},
            timeout=180,
        )

    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Falha ao enviar para o Telegram"))


def send_audio_to_worker_proxy(file_path, caption=""):
    if not telegram_proxy_enabled():
        return

    headers = {}
    if config.TELEGRAM_PROXY_SECRET:
        headers["x-worker-secret"] = config.TELEGRAM_PROXY_SECRET

    with open(file_path, "rb") as audio_file:
        response = requests.post(
            config.TELEGRAM_PROXY_URL,
            data={
                "caption": (caption or f"Audio gerado pelo {config.APP_TITLE}")[:1024],
                "title": config.APP_TITLE,
                "performer": config.APP_AUTHOR,
                "disable_notification": "true" if config.TELEGRAM_SILENT else "false",
                "filename": os.path.basename(file_path),
            },
            files={"audio": (os.path.basename(file_path), audio_file, "audio/mpeg")},
            headers=headers,
            timeout=180,
        )

    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(payload.get("error", "Falha ao enviar para o Worker do Cloudflare"))


def prepare_downloadable_audio(audio_tuple, caption="audio"):
    cleanup_old_audio_files()
    wav_path = save_audio_tuple_to_wav(audio_tuple)
    wav_name = build_output_filename(caption, extension="wav")
    final_wav_path = os.path.join(tempfile.gettempdir(), wav_name)
    try:
        if os.path.exists(final_wav_path):
            os.remove(final_wav_path)
        os.replace(wav_path, final_wav_path)
    except OSError:
        final_wav_path = wav_path
    return final_wav_path


def notify_approved_download(file_path, caption="", last_sent_path=""):
    if not telegram_proxy_enabled() and not telegram_enabled():
        return last_sent_path
    if not file_path or not os.path.exists(file_path):
        return last_sent_path
    if file_path == last_sent_path:
        return last_sent_path
    mp3_path = None
    try:
        mp3_path = convert_wav_to_mp3(file_path, caption=caption)
        if telegram_proxy_enabled():
            send_audio_to_worker_proxy(mp3_path, caption=caption)
        else:
            send_audio_to_telegram(mp3_path, caption=caption)
    finally:
        if mp3_path and os.path.exists(mp3_path):
            try:
                os.remove(mp3_path)
            except OSError:
                pass
    return file_path


def load_model(status_callback=None):
    global MODEL, SAMPLING_RATE
    if MODEL is not None:
        return MODEL

    if status_callback:
        status_callback("Baixando e iniciando modelo OmniVoice", "Carregando modelo na GPU T4...", 90)

    MODEL = OmniVoice.from_pretrained(
        config.MODEL_ID,
        device_map="cuda",
        dtype=torch.float16,
        load_asr=True,
        token=False,
    )
    SAMPLING_RATE = MODEL.sampling_rate
    return MODEL


def lang_dropdown():
    return gr.Dropdown(label="Language (optional)", choices=LANGUAGES, value="Auto")


def gen_settings():
    with gr.Accordion("Advanced Settings", open=False):
        ns = gr.Slider(8, 64, value=config.DEFAULT_INFERENCE_STEPS, step=1, label="Inference Steps")
        gs = gr.Slider(0.0, 10.0, value=config.DEFAULT_GUIDANCE_SCALE, step=0.1, label="Guidance Scale")
        dn = gr.Slider(0.0, 1.0, value=config.DEFAULT_DENOISE_RATIO, step=0.05, label="Denoise Ratio")
        sp = gr.Slider(0.5, 2.0, value=config.DEFAULT_SPEED, step=0.05, label="Speed")
        du = gr.Slider(0, 30, value=config.DEFAULT_DURATION, step=0.5, label="Duration (0 = auto)")
        pp = gr.Checkbox(value=config.DEFAULT_PREPROCESS_PROMPT, label="Preprocess Prompt")
        po = gr.Checkbox(value=config.DEFAULT_POSTPROCESS_OUTPUT, label="Postprocess Output")
    return ns, gs, dn, sp, du, pp, po


def build_instruct(groups):
    selected = [group for group in groups if group and group != "Auto"]
    return ", ".join(selected) if selected else ""


def generate_speech(
    text,
    language,
    ref_audio,
    instruct,
    num_step,
    guidance_scale,
    denoise,
    speed,
    duration,
    preprocess_prompt,
    postprocess_output,
    mode="clone",
    ref_text=None,
):
    if not text or not text.strip():
        return None, "Please enter some text."

    model = load_model()

    lang_code = None
    if language and language != "Auto":
        lang_code = language.split("(")[-1].rstrip(")").strip() if "(" in language else language

    gen_config = OmniVoiceGenerationConfig(
        num_step=int(num_step or config.DEFAULT_INFERENCE_STEPS),
        guidance_scale=float(guidance_scale) if guidance_scale is not None else config.DEFAULT_GUIDANCE_SCALE,
        denoise=bool(denoise) if denoise is not None else True,
        preprocess_prompt=bool(preprocess_prompt),
        postprocess_output=bool(postprocess_output),
    )

    kwargs = {
        "text": text.strip(),
        "language": lang_code,
        "generation_config": gen_config,
    }

    if speed is not None and float(speed) != 1.0:
        kwargs["speed"] = float(speed)
    if duration is not None and float(duration) > 0:
        kwargs["duration"] = float(duration)

    if mode == "clone":
        if ref_audio is None:
            return None, "Please upload a reference audio."
        kwargs["voice_clone_prompt"] = model.create_voice_clone_prompt(
            ref_audio=ref_audio,
            ref_text=ref_text,
        )

    if mode == "design" and instruct and instruct.strip():
        kwargs["instruct"] = instruct.strip()

    try:
        audio = model.generate(**kwargs)
    except Exception as exc:
        return None, f"Error: {type(exc).__name__}: {exc}"

    waveform = audio[0].squeeze()
    if hasattr(waveform, "numpy"):
        waveform = waveform.numpy()
    waveform = (waveform * 32767).astype(np.int16)
    caption = text.strip() or f"Audio gerado pelo {config.APP_TITLE}"
    audio_path = prepare_downloadable_audio((SAMPLING_RATE, waveform), caption=caption)
    return audio_path, f"Generated {waveform.shape[-1] / SAMPLING_RATE:.1f}s audio at {SAMPLING_RATE}Hz", audio_path, caption


def create_app():
    with gr.Blocks(title=config.APP_TITLE, theme=gr.themes.Base(), css=CSS, head=HEAD) as demo:
        gr.HTML(BRAND_HTML)

        with gr.Tabs():
            with gr.TabItem("Voice Clone"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=5):
                        vc_text = gr.Textbox(
                            show_label=False,
                            lines=9,
                            placeholder="Digite aqui o texto que voce quer transformar em audio...",
                            elem_id="caixa-texto",
                        )
                    with gr.Column(scale=2, elem_id="coluna-direita"):
                        vc_ref_audio = gr.Audio(
                            label="Carregar audio de referencia",
                            type="filepath",
                            elem_id="caixa-audio",
                        )
                        vc_lang = lang_dropdown()
                        vc_lang.elem_id = "caixa-linguagem"
                        vc_btn = gr.Button("GERAR AUDIO", elem_id="botao-gerar")

                with gr.Row():
                    with gr.Column(scale=1):
                        vc_audio = gr.Audio(show_label=False, type="filepath", elem_id="caixa-resultado")
                        vc_audio_path = gr.State("")
                        vc_audio_caption = gr.State("")
                        vc_last_sent_path = gr.State("")
                        vc_telegram_trigger = gr.Button("telegram clone trigger", elem_id="telegram-clone-trigger")

                with gr.Accordion("Status e Configuracoes Extras", open=False):
                    vc_ref_text = gr.Textbox(
                        label="Reference Text (optional)",
                        lines=2,
                        placeholder="Transcript of ref audio. Leave empty for auto-transcription.",
                    )
                    vc_ns, vc_gs, vc_dn, vc_sp, vc_du, vc_pp, vc_po = gen_settings()
                    vc_status = gr.Textbox(label="Status", lines=2)

                def clone_fn(text, lang, ref_aud, ref_text, ns, gs, dn, sp, du, pp, po):
                    return generate_speech(
                        text,
                        lang,
                        ref_aud,
                        None,
                        ns,
                        gs,
                        dn,
                        sp,
                        du,
                        pp,
                        po,
                        mode="clone",
                        ref_text=ref_text or None,
                    )

                def approve_clone_download(file_path, caption, last_sent_path):
                    return notify_approved_download(file_path, caption, last_sent_path)

                vc_btn.click(
                    fn=lambda: (gr.update(value="GERANDO...", interactive=False), "Processando audio, aguarde..."),
                    inputs=None,
                    outputs=[vc_btn, vc_status],
                ).then(
                    fn=clone_fn,
                    inputs=[vc_text, vc_lang, vc_ref_audio, vc_ref_text, vc_ns, vc_gs, vc_dn, vc_sp, vc_du, vc_pp, vc_po],
                    outputs=[vc_audio, vc_status, vc_audio_path, vc_audio_caption],
                ).then(
                    fn=lambda: gr.update(value="GERAR AUDIO", interactive=True),
                    inputs=None,
                    outputs=[vc_btn],
                )

                vc_telegram_trigger.click(
                    fn=approve_clone_download,
                    inputs=[vc_audio_path, vc_audio_caption, vc_last_sent_path],
                    outputs=[vc_last_sent_path],
                )

            with gr.TabItem("Voice Design"):
                with gr.Row():
                    with gr.Column(scale=1):
                        vd_text = gr.Textbox(label="Text to Synthesize", lines=4, placeholder="Enter text here...")
                        vd_lang = lang_dropdown()
                        vd_groups = []
                        for category, choices in CATEGORIES.items():
                            vd_groups.append(
                                gr.Dropdown(label=category, choices=["Auto"] + choices, value="Auto", info=ATTR_INFO.get(category))
                            )
                        vd_ns, vd_gs, vd_dn, vd_sp, vd_du, vd_pp, vd_po = gen_settings()
                        vd_btn = gr.Button("Generate", variant="primary", size="lg")
                    with gr.Column(scale=1):
                        vd_audio = gr.Audio(label="Output Audio", type="filepath", elem_id="design-resultado")
                        vd_audio_path = gr.State("")
                        vd_audio_caption = gr.State("")
                        vd_last_sent_path = gr.State("")
                        vd_telegram_trigger = gr.Button("telegram design trigger", elem_id="telegram-design-trigger")
                        vd_status = gr.Textbox(label="Status", lines=2)

                def design_fn(text, lang, ns, gs, dn, sp, du, pp, po, *groups):
                    return generate_speech(text, lang, None, build_instruct(groups), ns, gs, dn, sp, du, pp, po, mode="design")

                def approve_design_download(file_path, caption, last_sent_path):
                    return notify_approved_download(file_path, caption, last_sent_path)

                vd_btn.click(
                    fn=lambda: (gr.update(value="GERANDO...", interactive=False), "Processando audio, aguarde..."),
                    inputs=None,
                    outputs=[vd_btn, vd_status],
                ).then(
                    fn=design_fn,
                    inputs=[vd_text, vd_lang, vd_ns, vd_gs, vd_dn, vd_sp, vd_du, vd_pp, vd_po] + vd_groups,
                    outputs=[vd_audio, vd_status, vd_audio_path, vd_audio_caption],
                ).then(
                    fn=lambda: gr.update(value="Generate", interactive=True),
                    inputs=None,
                    outputs=[vd_btn],
                )

                vd_telegram_trigger.click(
                    fn=approve_design_download,
                    inputs=[vd_audio_path, vd_audio_caption, vd_last_sent_path],
                    outputs=[vd_last_sent_path],
                )

    return demo


def launch_app(share=None, inline=None, quiet=None):
    load_model()
    demo = create_app()
    return demo.queue().launch(
        share=config.GRADIO_SHARE if share is None else share,
        inline=config.GRADIO_INLINE if inline is None else inline,
        quiet=config.GRADIO_QUIET if quiet is None else quiet,
    )


if __name__ == "__main__":
    launch_app()
