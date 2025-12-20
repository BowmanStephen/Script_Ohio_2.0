/** @type {import('next').NextConfig} */
const path = require("path");

const nextConfig = {
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  // Set outputFileTracingRoot to repo root for proper file access
  // This allows Next.js to include files from repo root in the build
  outputFileTracingRoot: path.resolve(__dirname, ".."),
}

module.exports = nextConfig
