import type { Metadata } from "next";
import { Providers } from "@/components/Providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Research Assistant",
  description: "AI-powered research assistant with citation tracking",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased bg-zinc-950 text-zinc-100 h-screen overflow-hidden">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
