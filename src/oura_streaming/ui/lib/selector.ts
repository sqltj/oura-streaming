export function selector() {
  return {
    select: (response: { data: unknown }) => response.data,
  };
}
