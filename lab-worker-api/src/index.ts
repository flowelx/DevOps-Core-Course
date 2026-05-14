export interface Env {
	ENVIRONMENT: string;
	DEFAULT_MESSAGE: string;

	API_KEY?: string;
	ADMIN_EMAIL?: string;

	LAB_KV: KVNamespace;
}

export default {
  	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		const url = new URL(request.url);
		const path = url.pathname;
		const method = request.method;

		console.log(`[${new Date().toISOString()}] ${method} ${path} - ${request.headers.get('CF-Connecting-IP') || 'unknown'}`);

    	if (path === '/health') {
			console.log('Health check requested');
			const response = Response.json({
				status: 'ok',
				timestamp: new Date().toISOString(),
				uptime: performance.now()
			});
			console.log('Health check response sent, status: ok');
			return response;
		}

		if (path === '/meta') {
			console.log(`Metadata requested, environment: ${env.ENVIRONMENT}`);
			return Response.json({
				service: 'lab-worker-api',
				version: '2.0.0',
				environment: env.ENVIRONMENT,
				runtime: 'Cloudflare Workers',
				deployed_at: new Date().toISOString(),
				greeting: env.DEFAULT_MESSAGE,
				changelog: 'Added logging and monitoring'
			});
		}

		if (path === '/edge') {
			const cf = request.cf || {};
			console.log(`Edge metadata requested from colo: ${cf.colo || 'unknown'}, country: ${cf.country || 'unknown'}`);
			
			return Response.json({
				success: true,
				edge: {
					colo: cf.colo || 'local',
					country: cf.country || 'local',
					city: cf.city || 'localhost',
					httpProtocol: request.cf?.tlsVersion ? 'HTTPS' : request.url.split(':')[0],
					tlsVersion: cf.tlsVersion || 'N/A'
				},
				clientIp: request.headers.get('CF-Connecting-IP') || 'unknown'
			});
		}

		if (path === '/kv/save' && request.method === 'POST') {
			const url = new URL(request.url);
			const key = url.searchParams.get('key');
			const value = url.searchParams.get('value');

			console.log(`KV Save requested - key: ${key}, value length: ${value?.length || 0}`);
		
			if (!key || !value) {
				console.log(`KV Save failed - missing parameters: key=${!!key}, value=${!!value}`);
				return Response.json({ error: 'Missing key or value' }, { status: 400 });
			}
		
			await env.LAB_KV.put(key, value);
			console.log(`KV Save successful - key: ${key} stored`);
			return Response.json({ success: true, key, value });
		}

		if (path === '/kv/get') {
			const key = new URL(request.url).searchParams.get('key');
			console.log(`KV Get requested - key: ${key}`);

			if (!key) {
				console.log(`KV Get failed - missing key parameter`);
				return Response.json({ error: 'Missing key' }, { status: 400 });
			}
			
			const value = await env.LAB_KV.get(key);
			console.log(`KV Get result - key: ${key}, found: ${!!value}`);
			return Response.json({ key, value });
		}


		if (path === '/admin/status') {
			const userKey = request.headers.get('X-API-Key');
			console.log(`Admin status requested - auth attempt: ${userKey ? 'provided' : 'missing'}`);

			if (userKey !== env.API_KEY) {
				console.log(`Admin access denied - invalid API key`);
				return new Response('Forbidden', { status: 403 });
			}

			console.log(`Admin access granted - email: ${env.ADMIN_EMAIL}`);
			return Response.json({ adminEmail: env.ADMIN_EMAIL, status: 'active' });
		}


		if (path === '/') {
			console.log('Root endpoint accessed');
      		return Response.json({
        		message: 'Welcome to Cloudflare Workers API',
        		endpoints: ['/', '/health', '/meta', '/edge', '/kv/save', '/kv/get', '/admin/status']
      		});
    	}	

		console.log(`404 Not Found - ${method} ${path}`);
    	return new Response('Not Found', { status: 404 });
  	},
};