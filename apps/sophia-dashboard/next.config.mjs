/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: process.cwd(),
  },
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8082',
  },
  // Removed proxy rewrites - using direct API calls instead
};

export default nextConfig;