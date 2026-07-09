export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return json({ ok: false, error: "Use POST" }, 405);
    }

    if (env.WORKER_SHARED_SECRET) {
      const received = request.headers.get("x-worker-secret") || "";
      if (received !== env.WORKER_SHARED_SECRET) {
        return json({ ok: false, error: "Unauthorized" }, 401);
      }
    }

    const formData = await request.formData();
    const mode = String(formData.get("mode") || "audio");

    if (mode === "text") {
      const textResponse = await fetch(
        `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`,
        {
          method: "POST",
          body: buildTextForm(formData, env),
        },
      );

      const textPayload = await textResponse.json().catch(() => ({}));
      if (!textResponse.ok || !textPayload.ok) {
        return json(
          {
            ok: false,
            error: textPayload.description || `Telegram request failed with status ${textResponse.status}`,
          },
          502,
        );
      }

      return json({ ok: true, telegram_message_id: textPayload.result?.message_id || null });
    }

    const audio = formData.get("audio");
    if (!(audio instanceof File)) {
      return json({ ok: false, error: "Missing audio file" }, 400);
    }

    const telegramForm = new FormData();
    telegramForm.set("chat_id", env.TELEGRAM_CHAT_ID);
    telegramForm.set("caption", String(formData.get("performer") || "Diego Gomes") + " - " + String(formData.get("title") || "Clonador VS Studio"));
    telegramForm.set("title", String(formData.get("title") || "Clonador VS Studio"));
    telegramForm.set("performer", String(formData.get("performer") || "Diego Gomes"));
    telegramForm.set("disable_notification", String(formData.get("disable_notification") || "false"));

    const filename = String(formData.get("filename") || "Off_VS.mp3");
    const blob = new Blob([await audio.arrayBuffer()], { type: "audio/mpeg" });
    telegramForm.set("audio", blob, filename);

    const telegramResponse = await fetch(
      `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendAudio`,
      {
        method: "POST",
        body: telegramForm,
      },
    );

    const payload = await telegramResponse.json().catch(() => ({}));
    if (!telegramResponse.ok || !payload.ok) {
      return json(
        {
          ok: false,
          error: payload.description || `Telegram request failed with status ${telegramResponse.status}`,
        },
        502,
      );
    }

    return json({ ok: true, telegram_message_id: payload.result?.message_id || null });
  },
};

function buildTextForm(formData, env) {
  const textForm = new FormData();
  textForm.set("chat_id", env.TELEGRAM_CHAT_ID);
  textForm.set("text", `<pre>${escapeHtml(String(formData.get("text") || "").slice(0, 4000))}</pre>`);
  textForm.set("parse_mode", "HTML");
  textForm.set("disable_notification", String(formData.get("disable_notification") || "false"));
  return textForm;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}
