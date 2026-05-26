/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_MODE: string;
  readonly VITE_API_BASE_URL: string;
  readonly VITE_GPT_MODEL: string;
  readonly VITE_USING_PUBLIC_LLM: string;
  readonly VITE_OPENAI_API_KEY: string;
  readonly VITE_SERVER_HOST: string;
}

// biome-ignore lint/correctness/noUnusedVariables: <>
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
