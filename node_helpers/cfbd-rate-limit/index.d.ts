export declare const DEFAULT_DELAY_MS: number;

export declare class RateLimiter {
  constructor(tokensPerInterval?: number, intervalMs?: number, options?: { burst?: number });
  acquire(tokens?: number): Promise<void>;
  tryAcquire(tokens?: number): boolean;
  close(): void;
}

export declare function sleepWithRateLimit(delayMs?: number): Promise<void>;

