/// <reference path="../.astro/types.d.ts" />
/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly CWOI_HOST: string,
  readonly CWOI_NAME: string,
  readonly CWOI_PASSWORD: string,

  readonly AUTH_SECRET: string,

  readonly POSTGRES_URL: string,
};

interface ImportMeta {
  readonly env: ImportMetaEnv,
};