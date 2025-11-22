#!/usr/bin/env node
import { promises as fs } from "node:fs";
import path from "node:path";
import process from "node:process";

import { client, getAdvancedTeamStats, getGames, getLines } from "cfbd";
import { RateLimiter } from "@script-ohio/cfbd-rate-limit";

const {
  CFBD_API_KEY,
  CFBD_HOST,
  HYDRATE_SEASON = "2025",
  HYDRATE_WEEK = "12",
  HYDRATE_CLASSIFICATION = "fbs",
  HYDRATE_OUTPUT = "week12_digestible_analysis/visualizations/data/week12_payload.json",
  CFBD_RATE_LIMIT_MS = "170",
} = process.env;

if (!CFBD_API_KEY) {
  console.error("Missing CFBD_API_KEY environment variable.");
  process.exit(1);
}

const baseUrl = CFBD_HOST
  ? CFBD_HOST.startsWith("http")
    ? CFBD_HOST
    : `https://${CFBD_HOST}`
  : "https://api.collegefootballdata.com";

client.setConfig({
  baseUrl,
  headers: {
    Authorization: `Bearer ${CFBD_API_KEY}`,
  },
});

const limiter = new RateLimiter(1, Number(CFBD_RATE_LIMIT_MS) || 170);

async function fetchWithLimit(fn, params) {
  await limiter.acquire();
  const result = await fn(params);
  return result.data ?? [];
}

async function hydrate() {
  const season = Number(HYDRATE_SEASON);
  const week = Number(HYDRATE_WEEK);

  const [games, advancedStats, lines] = await Promise.all([
    fetchWithLimit(getGames, {
      query: {
        year: season,
        week,
        classification: HYDRATE_CLASSIFICATION,
      },
    }),
    fetchWithLimit(getAdvancedTeamStats, {
      query: { year: season, seasonType: "regular" },
    }),
    fetchWithLimit(getLines, {
      query: { year: season, week },
    }),
  ]);

  const payload = {
    generatedAt: new Date().toISOString(),
    season,
    week,
    classification: HYDRATE_CLASSIFICATION,
    baseUrl,
    games,
    advancedStats,
    lines,
  };

  const outputPath = path.resolve(HYDRATE_OUTPUT);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, JSON.stringify(payload, null, 2));
  console.log(`Hydration payload saved to ${outputPath}`);
}

hydrate()
  .catch((error) => {
    console.error("Hydration script failed:", error);
    process.exitCode = 1;
  })
  .finally(() => {
    limiter.close();
  });

