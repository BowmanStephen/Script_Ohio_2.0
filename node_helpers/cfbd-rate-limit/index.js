/**
 * Token bucket rate limiter tuned for CollegeFootballData.com API usage.
 * Provides awaitable acquire() calls plus a simple sleep helper.
 */
const DEFAULT_DELAY_MS = 170; // 0.17 seconds => 6 req/sec

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

class RateLimiter {
  /**
   * @param {number} tokensPerInterval Tokens added each interval (default 1).
   * @param {number} intervalMs Interval length in ms (default 170ms).
   * @param {{burst?: number}} options Optional burst capacity override.
   */
  constructor(tokensPerInterval = 1, intervalMs = DEFAULT_DELAY_MS, options = {}) {
    if (!(tokensPerInterval > 0)) {
      throw new Error("tokensPerInterval must be > 0");
    }
    if (!(intervalMs > 0)) {
      throw new Error("intervalMs must be > 0");
    }

    this.tokensPerInterval = tokensPerInterval;
    this.intervalMs = intervalMs;
    this.burst = Math.max(
      typeof options.burst === "number" ? options.burst : tokensPerInterval,
      tokensPerInterval
    );

    this.tokens = this.burst;
    this.queue = [];
    this._refillHandle = setInterval(() => this._refill(), this.intervalMs);
    this._refillHandle.unref?.(); // allow process exit when idle (Node >=10)
  }

  _refill() {
    this.tokens = Math.min(this.tokens + this.tokensPerInterval, this.burst);
    this._drainQueue();
  }

  _drainQueue() {
    while (this.queue.length > 0) {
      const request = this.queue[0];
      if (this.tokens >= request.tokens) {
        this.tokens -= request.tokens;
        this.queue.shift();
        request.resolve();
      } else {
        break;
      }
    }
  }

  /**
   * Acquire n tokens, waiting if necessary.
   * @param {number} tokens
   * @returns {Promise<void>}
   */
  acquire(tokens = 1) {
    const tokensNeeded = Math.max(tokens, 1);
    return new Promise((resolve) => {
      if (this.tokens >= tokensNeeded && this.queue.length === 0) {
        this.tokens -= tokensNeeded;
        resolve();
      } else {
        this.queue.push({ tokens: tokensNeeded, resolve });
      }
    });
  }

  /**
   * Try to acquire tokens without waiting.
   * @param {number} tokens
   * @returns {boolean}
   */
  tryAcquire(tokens = 1) {
    const tokensNeeded = Math.max(tokens, 1);
    if (this.tokens >= tokensNeeded && this.queue.length === 0) {
      this.tokens -= tokensNeeded;
      return true;
    }
    return false;
  }

  /**
   * Stop the refill interval and clear the queue.
   */
  close() {
    if (this._refillHandle) {
      clearInterval(this._refillHandle);
      this._refillHandle = null;
    }
    this.queue.splice(0, this.queue.length);
  }
}

async function sleepWithRateLimit(delayMs = DEFAULT_DELAY_MS) {
  await sleep(delayMs);
}

module.exports = {
  RateLimiter,
  sleepWithRateLimit,
  DEFAULT_DELAY_MS,
};

