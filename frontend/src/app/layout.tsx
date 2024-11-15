import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Skip AI',
  description: 'Interactive Search for Skip Podcast',
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/skip-logo-16.png', sizes: '16x16', type: 'image/png' },
      { url: '/skip-logo-32.png', sizes: '32x32', type: 'image/png' },
      { url: '/skip-logo.png', sizes: '192x192', type: 'image/png' },
    ],
    apple: [
      { url: '/skip-logo-apple.png', sizes: '180x180', type: 'image/png' },
    ],
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/skip-logo.png" />
        <link rel="apple-touch-icon" href="/skip-logo-apple.png" />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  );
}