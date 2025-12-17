# CFBD Data Audit Report — 2025

- Generated (UTC): `2025-12-17T05:14:05+00:00`
- Starter data dir: `starter_pack/data`

## Expected Index (from games.csv)

- Expected games: **1676**
- Expected weeks: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]`

## Dataset Completeness

### game_stats

- Path: `starter_pack/data/game_stats/2025.csv`
- Exists: **True**
- Game IDs present: **1489 / 1676**
- Missing gameIds: **208**
  - First 20: `[401752773, 401752774, 401752775, 401752776, 401752777, 401752778, 401752779, 401752780, 401752781, 401752782, 401752908, 401752909, 401752910, 401752911, 401752912, 401752913, 401752914, 401752915, 401752954, 401754598]`
- Weeks present: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16]`
- Missing weeks: **1** → `[13]`

### advanced_game_stats

- Path: `starter_pack/data/advanced_game_stats/2025.csv`
- Exists: **True**
- Game IDs present: **1384 / 1676**
- Missing gameIds: **301**
  - First 20: `[401752773, 401752774, 401752775, 401752776, 401752777, 401752778, 401752779, 401752780, 401752781, 401752782, 401752783, 401752784, 401752785, 401752786, 401752787, 401752788, 401752789, 401752790, 401752791, 401752792]`
- Weeks present: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]`
- Missing weeks: **3** → `[13, 14, 16]`

### drives

- Path: `starter_pack/data/drives/drives_2025.csv`
- Exists: **True**
- Game IDs present: **1385 / 1676**
- Missing gameIds: **300**
  - First 20: `[401752773, 401752774, 401752775, 401752776, 401752777, 401752778, 401752779, 401752780, 401752781, 401752782, 401752783, 401752784, 401752785, 401752786, 401752787, 401752788, 401752789, 401752790, 401752791, 401752792]`
- Weeks present: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]`
- Missing weeks: **3** → `[13, 14, 16]`

### season_stats

- Path: `starter_pack/data/season_stats/2025.csv`
- Exists: **True**
- Game IDs present: **0 / 1676**
- Weeks present: `[]`
- Missing weeks: **15** → `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]`
- Notes:
  - Could not find a game id column in starter_pack/data/season_stats/2025.csv (looked for ['gameId', 'game_id', 'id', 'gameID']); gameId checks skipped.
  - Could not find week in starter_pack/data/season_stats/2025.csv and could not infer from games.csv.

### advanced_season_stats

- Path: `starter_pack/data/advanced_season_stats/2025.csv`
- Exists: **True**
- Game IDs present: **0 / 1676**
- Weeks present: `[]`
- Missing weeks: **15** → `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]`
- Notes:
  - Could not find a game id column in starter_pack/data/advanced_season_stats/2025.csv (looked for ['gameId', 'game_id', 'id', 'gameID']); gameId checks skipped.
  - Could not find week in starter_pack/data/advanced_season_stats/2025.csv and could not infer from games.csv.

### plays

- Path: `starter_pack/data/plays/2025`
- Exists: **True**
- Weeks present: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]`
- Notes:
  - Found 15 plays CSV files.

## Postseason (online index)

- Online enabled: **True**
- Online available: **True**
- Expected postseason games (CFBD): **77**
- Missing from games.csv: **0**
