# 🏈 College Football Model Pack: Data Info Sheet

This dataset includes **cleaned, opponent-adjusted college football data** for FBS games from **Week 5 through postseason**, covering the **2016–2025** seasons (2025 season data includes weeks 1-12 as of latest update).

Each row represents a single game, with team statistics based on games played **prior to that matchup only**, ensuring no leakage of future results.



The dataset is ideal for training machine learning models to predict outcomes like:
- Final score or score margin
- Win probability
- Spread cover probability
- Offensive or defensive efficiency

Fields with the word `"adjusted"` represent **opponent-adjusted metrics**, calculated to account for schedule strength up to the point of the game.

---

## 🔢 Dataset Size and Features

Each row includes **88 total columns**, consisting of:

- **81 feature columns** for training predictive models (including season, week, home_team, away_team, neutral_site, team strength metrics, scoring metrics, and 68 opponent-adjusted features)
- **7 metadata columns** (id, game_key, conference_game, start_date, season_type, home_conference, away_conference)

**Note on Feature Counting:**
- The 81 features include base metrics (season, week, teams, neutral_site), team strength (Elo, talent), scoring (points, margin, spread), and all opponent-adjusted metrics
- Some validation scripts may reference "86 features" - this is a documentation discrepancy. The actual feature count is **81 features** as defined above
- Metadata columns (id, game_key, etc.) are excluded from the feature count as they are identifiers, not predictive features

The dataset has been structured to separate features from targets and identifiers, making it easy to plug into model pipelines with minimal preprocessing.

---

## 🗂️ Field Groupings & Descriptions

### 🏷️ Game Metadata
| Field | Description |
|-------|-------------|
| `id` | Unique game identifier |
| `start_date` | Date of the game |
| `season` | Season year |
| `season_type` | Regular or postseason |
| `week` | Week number |
| `neutral_site` | True if played at a neutral site |
| `spread` | Vegas closing spread (negative = home favored) |

---

### 🏠 Home Team Info
| Field | Description |
|-------|-------------|
| `home_team` | Home team name |
| `home_conference` | Home team’s conference |
| `home_elo` | Pre-game Elo rating |
| `home_talent` | Team talent composite rating |

---

### 🛫 Away Team Info
| Field | Description |
|-------|-------------|
| `away_team` | Away team name |
| `away_conference` | Away team’s conference |
| `away_elo` | Pre-game Elo rating |
| `away_talent` | Team talent composite rating |

---

### 🏁 Game Outcome
| Field | Description |
|-------|-------------|
| `home_points` | Final home score |
| `away_points` | Final away score |
| `margin` | Final score margin (home - away) |

---

### 📊 Opponent-Adjusted EPA (Efficiency)
| Field | Description |
|-------|-------------|
| `home_adjusted_epa`, `away_adjusted_epa` | Overall adjusted EPA per play |
| `home_adjusted_epa_allowed`, `away_adjusted_epa_allowed` | Defensive adjusted EPA allowed |

---

### 🏃 Opponent-Adjusted Rushing & Passing EPA
| Field | Description |
|-------|-------------|
| `*_adjusted_rushing_epa`, `*_adjusted_passing_epa` | Offensive rushing/passing EPA |
| `*_adjusted_rushing_epa_allowed`, `*_adjusted_passing_epa_allowed` | Defensive EPA allowed |

---

### 📈 Opponent-Adjusted Success Rates
| Field | Description |
|-------|-------------|
| `*_adjusted_success` | Overall success rate |
| `*_adjusted_standard_down_success`, `*_adjusted_passing_down_success` | Down-specific success rates |
| `*_adjusted_success_allowed` | Overall success rate allowed on defense |
| `*_adjusted_standard_down_success_allowed`, `*_adjusted_passing_down_success_allowed` | Down-specific success rates allowed on defense |

---

### 🧱 Opponent-Adjusted Line Yardage Metrics
| Field | Description |
|-------|-------------|
| `*_adjusted_line_yards` | Line yards per carry |
| `*_adjusted_second_level_yards` | Second-level yards per carry |
| `*_adjusted_open_field_yards` | Open-field yards per carry |
| `*_allowed` variants | Defensive equivalents |

---

### 💥 Opponent-Adjusted Explosiveness Metrics
| Field | Description |
|-------|-------------|
| `*_adjusted_explosiveness` | Overall explosiveness (EPA/play on successful plays) |
| `*_adjusted_rush_explosiveness`, `*_adjusted_pass_explosiveness` | By play type |
| `*_allowed` variants | Defensive equivalents |

---

### 🔨 Havoc Metrics
| Field | Description |
|-------|-------------|
| `*_total_havoc_offense`, `*_front_seven_havoc_offense`, `*_db_havoc_offense` | Havoc rates allowed (offensive failures) |
| `*_total_havoc_defense`, `*_front_seven_havoc_defense`, `*_db_havoc_defense` | Havoc created (defensive disruption) |

---

### 🏁 Points Per Opportunity
| Field | Description |
|-------|-------------|
| `*_points_per_opportunity_offense` | Avg points per drive inside opponent 40 |
| `*_points_per_opportunity_defense` | Avg points allowed per opponent scoring opportunity |

---

### 🧭 Field Position
| Field | Description |
|-------|-------------|
| `*_avg_start_offense` | Average starting field position on offense |
| `*_avg_start_defense` | Average field position allowed on defense |

---

## 🧠 Ideal Use Cases
- Train predictive models for picks and spreads
- Analyze efficiency and explosiveness in context
- Study the relative strength of teams week-to-week

---

For support and usage examples, visit [collegefootballdata.com](https://collegefootballdata.com) or join the CFBD Discord community.
