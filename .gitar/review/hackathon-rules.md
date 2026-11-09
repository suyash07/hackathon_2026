# Hackathon rules

- Flag any secret: API keys (`sk-ant…`, `sk-proj…`, `sk-…`), passwords, tokens, or a committed `.env` file. Credentials belong only in `.env` (git-ignored); `.env.example` must have empty values.
- All attendee, speaker and talk data is synthetic. Flag real-looking personal data (real emails, phone numbers, addresses).
- Never use the term "eBPF" in code, data, UI text, examples or docs; use "kernel-level" / "kernel tracing".
- LLM text generation goes only through Elasticsearch's inference API (`es.inference.completion`). Flag any LLM SDK use for generation.
- One allowed exception: speech-to-text. `src/voice.py` may import `openai` and call `audio.transcriptions` only, because Elasticsearch has no speech-to-text. Flag `openai` imported anywhere else, or used for chat/completions. The key comes from `config.OPENAI_API_KEY` (pod: optional key `openai-api-key` in Secret `app-credentials`).
- README must keep the "AI use disclosure" section and up-to-date setup steps.
