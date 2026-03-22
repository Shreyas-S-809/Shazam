/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "i.scdn.co" },
      { protocol: "https", hostname: "i.ytimg.com" },
    ],
  },
  // Proxy all /api/* requests to the FastAPI backend.
  // This avoids CORS entirely — the browser only talks to localhost:3000.
  // Note: Next.js App Router API routes (e.g. /api/audio/recognize) take
  // priority over rewrites, so the upload route handler is used for that path.
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
