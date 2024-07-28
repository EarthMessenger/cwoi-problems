import type { APIRoute } from "astro";
import { createHmac, randomBytes } from "crypto";

const { AUTH_SECRET } = import.meta.env;

export const GET: APIRoute = async ({ request }) => {
  const searchParams = (new URL(request.url)).searchParams;

  if (!searchParams.has("name")) {
    return new Response(null, { status: 400 })
  }

  const name = searchParams.get("name");
  const challenge = randomBytes(3).toString("hex");
  const expireTime = (+(new Date()) + 10 * 60 * 1000).toString();
  const hmac = createHmac("sha256", AUTH_SECRET).update(`${name}|${challenge}|${expireTime}`).digest("base64");

  return new Response(JSON.stringify({
    name,
    challenge,
    expireTime,
    hmac
  }), {
    headers: {
      "Content-Type": "application/json",
    },
  });
}