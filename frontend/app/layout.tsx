import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "Song Shazam Pro — AI Song Recognition",
  description:
    "Record, recognize, and discover music instantly. Powered by AI audio fingerprinting with beautiful visualizations.",
  keywords: ["song recognition", "shazam", "music", "AI", "audio fingerprint"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-mesh min-h-screen">
        {/* Ambient gradient orbs */}
        <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
          <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-brand-green/5 blur-[120px]" />
          <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-accent-indigo/5 blur-[120px]" />
        </div>

        <main className="relative z-0">{children}</main>

        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              background: "rgba(17,17,17,0.9)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: "#fff",
              backdropFilter: "blur(12px)",
            },
          }}
        />
      </body>
    </html>
  );
}
