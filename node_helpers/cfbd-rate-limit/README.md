# @script-ohio/cfbd-rate-limit

Token-bucket rate limiter tuned for CollegeFootballData.com API usage. Mirrors the
official 6 requests/second guidance (0.17 s delay) so TypeScript/Node dashboards can
stay in sync with the Python agents and notebooks.

## Installation

```bash
npm install cfbd @script-ohio/cfbd-rate-limit
# or add the local package
npm install cfbd ../node_helpers/cfbd-rate-limit
```

## Usage

```ts
import { client, getGames } from "cfbd";
import { RateLimiter } from "@script-ohio/cfbd-rate-limit";

client.setConfig({
  headers: { Authorization: `Bearer ${process.env.CFBD_API_KEY}` },
});

const limiter = new RateLimiter(1, 170);

async function fetchGames() {
  await limiter.acquire();
  const result = await getGames({ query: { year: 2025, week: 12, classification: "fbs" } });
  return result.data ?? [];
}

fetchGames()
  .then((games) => console.log(`Fetched ${games.length} games`))
  .finally(() => limiter.close());
```

### API

| Export | Description |
| --- | --- |
| `RateLimiter` | Token bucket class with `acquire(tokens)`, `tryAcquire(tokens)`, `close()` |
| `sleepWithRateLimit(delayMs?)` | Simple awaitable sleep helper (defaults to 170 ms) |
| `DEFAULT_DELAY_MS` | Exposed constant (170) |

## License

MIT © Script Ohio 2.0

