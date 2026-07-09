import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: false, // registro manual en main.tsx para forzar recarga cuando hay versión nueva
      workbox: {
        clientsClaim: true,
        skipWaiting: true,
        // Cachea las respuestas GET de la API para poder ver tu garaje,
        // plan, historial y papeles sin señal (los datos pueden quedar
        // desactualizados, pero no queda una pantalla en blanco).
        runtimeCaching: [
          {
            urlPattern: ({ url, request }) =>
              request.method === 'GET' && url.pathname.startsWith('/api/'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 7 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      manifest: {
        name: 'MiGaraje — La bitácora inteligente de tu auto',
        short_name: 'MiGaraje',
        description:
          'Mantenimiento, kilometraje, facturas y papeles de tus autos: SOAT, revisión técnica, impuesto vehicular y brevete.',
        lang: 'es-PE',
        display: 'standalone',
        start_url: '/',
        theme_color: '#070D1B',
        background_color: '#070D1B',
        icons: [
          { src: '/pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/pwa-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
    }),
  ],
  server: {
    host: true, // accesible desde el celular vía wifi
  },
})
