export default {
  fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/') {
      return env.ASSETS.fetch(new URL('/index.html', url));
    }

    return env.ASSETS.fetch(request);
  },
};
