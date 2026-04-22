import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Apartments.com Clone",
  description: "Apartments.com-style rental search experience (clone).",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
