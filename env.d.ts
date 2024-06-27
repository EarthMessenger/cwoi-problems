/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly CWOI_HOST: string,
  readonly CWOI_NAME: string,
  readonly CWOI_PASSWORD: string,
};

interface ImportMeta {
  readonly env: ImportMetaEnv,
};