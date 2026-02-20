import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    // This repo has multiple lockfiles; explicitly pin the UI root to silence Next.js warnings.
    root: __dirname,
  },

  // Avoid dev-mode CORS/origin warnings when the dev server is accessed via 127.0.0.1.
  // (Next config expects this under `experimental` in some versions.)
  experimental: {
    allowedDevOrigins: ["http://127.0.0.1:3005", "http://localhost:3005"],
  },
};

export default nextConfig;
