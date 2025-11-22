const { RateLimiter } = require("../index.js");

async function demo() {
  const limiter = new RateLimiter(2, 1000, { burst: 2 });
  const start = Date.now();
  for (let i = 1; i <= 4; i += 1) {
    await limiter.acquire();
    console.log(`acquired ${i} at +${Date.now() - start}ms`);
  }
  limiter.close();
}

demo().catch((err) => {
  console.error(err);
  process.exit(1);
});

