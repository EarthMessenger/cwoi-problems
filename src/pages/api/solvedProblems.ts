import type { APIRoute } from "astro";

const getToken = async (cwoiHost: string, cwoiName: string, cwoiPassword: string) => {
  return fetch(`${cwoiHost}/api/user/login`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      login: cwoiName,
      password: cwoiPassword,
      remember: true,
    }),
  }).then(r => r.json())
    .then(r => r.token);
};

const getIdFromHandle = async (cwoiHost: string, handle: string) => {
  return fetch(`${cwoiHost}/api/user/info/handle/${handle}`)
    .then((r) => r.json())
    .then((r) => r._id);
}

export const GET: APIRoute = async ({ request, locals }) => {
  const { CWOI_HOST, CWOI_NAME, CWOI_PASSWORD } = locals.runtime.env;
  const token = await getToken(CWOI_HOST, CWOI_NAME, CWOI_PASSWORD);
  const url = request.url;
  const searchParams = new URLSearchParams(url.substring(url.indexOf('?')));
  const handle = searchParams.get('handle');
  const id = await getIdFromHandle(CWOI_HOST, handle);

  return fetch(`${CWOI_HOST}/api/user/${id}/solvedProblems`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }).then((r) => r.json())
    .then((r) => r.filter((p) => !p.cachedUrl.startsWith('/problem/')).map((p) => {
      const part = p.cachedUrl.split('/');
      return {
        contestId: part[2],
        problemId: part[4],
      };
    })).then((r) => Response.json(r));
}
