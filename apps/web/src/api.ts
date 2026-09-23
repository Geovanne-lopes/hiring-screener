export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function parse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (data as { detail?: unknown }).detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg || JSON.stringify(d)).join(" ")
          : res.statusText;
    throw new ApiError(msg || "Erro na API");
  }
  return data as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return fetch(path).then((r) => parse<T>(r));
}

export function apiSend<T>(path: string, method: string, body?: unknown): Promise<T> {
  return fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  }).then((r) => parse<T>(r));
}

export function apiForm<T>(path: string, form: FormData): Promise<T> {
  return fetch(path, { method: "POST", body: form }).then((r) => parse<T>(r));
}
