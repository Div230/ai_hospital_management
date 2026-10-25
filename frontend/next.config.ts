import type { NextConfig } from "next";

const backend = (process.env.API_INTERNAL_URL || "http://localhost:8000").replace(/\/+$/, "");
const nextConfig: NextConfig = {
  output: "standalone",
  // Django API routes are slash-terminated. Next's default redirect strips
  // that slash before proxying, causing unsafe-method redirects in Django.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    // Accept both URL forms and send Django its canonical URL directly.
    // This also covers signed document links and requests outside Axios.
    return [
      { source: "/api/:path*/", destination: `${backend}/api/:path*/` },
      { source: "/api/:path*", destination: `${backend}/api/:path*/` },
    ];
  },
  async headers() {
    return [{ source: "/:path*", headers: [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "same-origin" },
      { key: "X-Frame-Options", value: "DENY" },
    ] }];
  },
};
export default nextConfig;
