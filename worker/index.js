export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({
        ok: true,
        service: "agentic-product-studio-worker-bootstrap",
        hasDbBinding: Boolean(env.DB),
        hasImageBucketBinding: Boolean(env.DOCUMENT_IMAGES),
      });
    }

    return Response.json({
      message: "Cloudflare Worker bootstrap is ready.",
      nextStep: "Port Flask routes and data access into the Worker runtime.",
    });
  },
};
