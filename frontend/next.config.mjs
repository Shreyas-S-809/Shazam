/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export", // ✅ REQUIRED for Netlify

  images: {
    unoptimized: true, // ✅ required for static export
    remotePatterns: [
      { protocol: "https", hostname: "i.scdn.co" },
      { protocol: "https", hostname: "i.ytimg.com" },
    ],
  },
};

export default nextConfig;