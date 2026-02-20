import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    // This repo has multiple lockfiles; explicitly pin the UI root to silence Next.js warnings.
    root: __dirname,
  },
};

export default nextConfig;
