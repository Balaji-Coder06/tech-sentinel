import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Sidebar } from '../components/Sidebar';
import { MobileNav } from '../components/MobileNav';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
  title: 'Tech Sentinel',
  description: 'Personal AI-powered technology intelligence agent and free opportunity radar.',
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
      { url: '/icon', sizes: '32x32', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-icon', sizes: '180x180', type: 'image/png' },
    ],
  },
  manifest: '/manifest.webmanifest',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans bg-sentinel-bg text-sentinel-text min-h-screen flex flex-col lg:flex-row antialiased`}>
        {/* Persistent Desktop Sidebar */}
        <Sidebar />

        {/* Main Application Canvas */}
        <div className="flex-1 flex flex-col min-w-0 pb-20 lg:pb-0">
          {children}
        </div>

        {/* Mobile Bottom Navigation */}
        <MobileNav />
      </body>
    </html>
  );
}
