// Server routes for SSR - simplified for now
export const serverRoutes = [
  {
    path: '**',
    renderMode: 'prerender' as const
  }
];
