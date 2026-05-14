export interface Env {
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === '/health') {
      return Response.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        uptime: performance.now()
      });
    }

    if (path === '/meta') {
      return Response.json({
        service: 'lab-worker-api',
        version: '1.0.0',
        environment: 'production',
        runtime: 'Cloudflare Workers',
        deployed_at: new Date().toISOString()
      });
    }

    if (path === '/') {
      return Response.json({
        message: 'Welcome to Cloudflare Workers API',
        endpoints: ['/health', '/meta']
      });
    }

    return new Response('Not Found', { status: 404 });
  },
};