export const customFetch = async <T>({
  url,
  method,
  params,
  data,
}: {
  url: string;
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  params?: Record<string, string>;
  data?: unknown;
  headers?: Record<string, string>;
}): Promise<T> => {
  const searchParams = params
    ? `?${new URLSearchParams(params).toString()}`
    : "";

  const response = await fetch(`${url}${searchParams}`, {
    method,
    ...(data ? { body: JSON.stringify(data) } : {}),
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
};
