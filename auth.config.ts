import { defineConfig } from "auth-astro";
import Credentials from "@auth/core/providers/credentials"
import { createHmac } from "crypto";
import { z } from "zod";

const credentialSchema = z.object({
  name: z.string(),
  challenge: z.string().length(6),
  expireTime: z.string(),
  hmac: z.string().base64(),
})

export type CredentialSchema = z.infer<typeof credentialSchema>;

const { AUTH_SECRET, CWOI_HOST } = import.meta.env;

export default defineConfig({
  providers: [
    Credentials({
      credentials: {
        name: {},
        challenge: {},
        expireTime: {},
        hmac: {},
      },
      authorize: async (credential: CredentialSchema) => {
        try {
          const { name, challenge, expireTime, hmac } = await credentialSchema.parseAsync(credential);

          if (parseInt(expireTime) < +(new Date())) {
            throw new Error("challenge expired.");
          }

          if (createHmac("sha256", AUTH_SECRET).update(`${name}|${challenge}|${expireTime}`).digest("base64") !== hmac) {
            throw new Error("hmac not match.");
          }

          const motto = await fetch(`${CWOI_HOST}/api/user/info/handle/${encodeURIComponent(name)}`)
            .then((r) => r.json())
            .then((r) => r['motto']) as string;

          if (!motto.startsWith(challenge)) {
            throw new Error("challenge failed.");
          }

          return { name };
        } catch (e) {
          console.error(e);
          return null;
        }
      },
    }),
  ],
});
