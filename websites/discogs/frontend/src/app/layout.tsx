import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { CookieBanner } from "@/components/CookieBanner";

export const metadata: Metadata = {
  title: "Discogs",
  description: "Discogs clone",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-white text-neutral-900 antialiased">
        <Header />
        <CookieBanner />
        <div className="min-h-[70vh]">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
