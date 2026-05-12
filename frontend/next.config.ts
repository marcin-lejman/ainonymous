import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy /api/* to the FastAPI backend (used in combined Docker container
  // where both services share one host; harmless in local dev when
  // NEXT_PUBLIC_API_URL points the browser directly at the backend).
  rewrites: async () => [
    {
      source: "/api/:path*",
      destination: "http://127.0.0.1:8000/api/:path*",
    },
  ],
};

export default nextConfig;
