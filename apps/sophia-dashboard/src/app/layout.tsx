import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Sophia AI - Intelligent Multi-Agent Platform",
  description: "Advanced AI platform with agent orchestration, deep web research, code generation, and GitHub integration",
  icons: {
    icon: '/sophia-logo.jpg',
    shortcut: '/sophia-logo.jpg',
    apple: '/sophia-logo.jpg',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}