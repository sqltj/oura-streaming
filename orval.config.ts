import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: {
      target: "http://localhost:8000/openapi.json",
    },
    output: {
      target: "./ui/lib/api.ts",
      client: "react-query",
      mode: "single",
      override: {
        mutator: {
          path: "./ui/lib/fetcher.ts",
          name: "customFetch",
        },
        query: {
          useSuspenseQuery: true,
        },
      },
    },
  },
});
