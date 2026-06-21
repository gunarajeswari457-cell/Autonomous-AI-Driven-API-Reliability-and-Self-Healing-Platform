const API_UPSTREAM = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${API_UPSTREAM.replace(/\/$/, "")}/api/:path*` }
    ];
  }
};

export default nextConfig;
