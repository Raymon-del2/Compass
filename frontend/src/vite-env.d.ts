/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_COMPASS_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
