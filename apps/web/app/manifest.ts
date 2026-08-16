import { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Tech Sentinel — Opportunity Intelligence',
    short_name: 'Tech Sentinel',
    description: 'Personal AI-powered technology intelligence agent and free opportunity radar.',
    start_url: '/',
    display: 'standalone',
    background_color: '#111111',
    theme_color: '#FF5A36',
    icons: [
      {
        src: '/icon.svg',
        sizes: 'any',
        type: 'image/svg+xml',
      },
      {
        src: '/icon',
        sizes: '32x32',
        type: 'image/png',
      },
      {
        src: '/apple-icon',
        sizes: '180x180',
        type: 'image/png',
      },
    ],
  };
}
