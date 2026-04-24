# VlrBot

## Summary
A Valorant bot (v2.0.0) that uses web scraping with Selenium on vlr.gg to archive data from VCT matches. It analyzes this data and makes it available for visualization via Discord. We use a PostgreSQL database (hosted on Neon Tech's free plan) to store information about teams and matches. 
On-discord commands: 
  - `help_times`: show you a list of each team with it's emote so you know how to search for them in `info_time`.
  - `info_time`: show you a "book". First page has the last 5 matches played by this team; Second page shows the win rate of each composition used in each in-pool map played by the team (team that haven't been played yet will show "missing information", but in portuguese)

### v2.1.0
Now the bot also tracks the performance table from each active tournament (linked to `campeonatos`, see [Database](README.md#database)), capturing metrics like Rating, ACS and ADR to provide deeper match analysis. 

### v2.2.0
Now we can access the information stored in `stats_players`. `info_time` Shows the mean stats of the last tournament (mean of the ACS of each players, for example. Clutches are shown in the format `won/played`, being won and played the sum instead of the mean) in the first page. It also recieved a third page that contais the 'historical stats'. It works the same as the stats of the last tournament, but using data from all the tournaments registered.

### v2.2.1
**Search Normalization:** Users no longer need to include diacritics to find teams. For example, searching for "kru" will now correctly match "KRÜ".


---

## Files & Directory Structure
| File/Folder | Type | Summary |
| :------- | :--: | :------ |
| [Starting v2](./src/starting%20v2.ipynb) | `.ipynb` | Initial planning and first steps for the SQL database. |
| [Auto](./src/auto.py) | `.py` | Web scraping logic featuring `vlr_stealer` and `stats_manager` classes. |
| [DB_handler](./src/DB_handler.py) | `.py` | INSERT logic handled by the `DB_handler` class. |
| [Auto_scrapper.py](./src/auto_scrapper.py) | `.py` | Integration of `auto.py` and `DB_handler.py` (Scraping then inserting into DB). |
| [Disc_buttons](./src/disc_buttons.py) | `.py` | Interactive buttons for navigating Discord embeds. |
| [Main](./src/main.py) | `.py` | Core Discord bot logic. |
| [Brain](./src/brain.py) | `.py` | **Back-end logic:** handles database, caching, and data analysis |
| [Scrapper](./.github/workflows/scrapper.yml) | `.yml` | Automation logic for GitHub Actions. |
| [Agents](./assets/agents) | `dir/ .png` | PNG files used to create Discord emojis for each agent. |
| [Teams](./assets/teams) | `dir/ .png` | PNG files used to create Discord emojis for each team. |
| [DB Sch](./assets/DB%20Sch.svg) | `.svg` | Database Schema diagram. |

---

## Database

![Database Schema](./assets/DB%20Sch.svg)
<sub>**Data Mapping Note:** `stat_players` table may raise errors during insertion if a record contains "N/A". This usually happens when a team changes its tag on vlr.gg (e.g., when DRX changed to KRX), causing a mismatch with the existing database records. While new players are added automatically, team tags must be updated manually in the `times` table to maintain Referential Integrity.</sub>

Hosted on PostgreSQL (Neon Tech free plan: 0.5GB storage, 100 CU-hours). The database consists of 7 tables. Descriptions of Portuguese attributes:
- **Agentes**: Agents ('nome' = name)
- **Mapas_lista**: Map list
- **Composicoes**: Team compositions
- **Mapas_jogados**: Played maps ('vencedor_mapa' = map winner)
- **Partidas**: Matches ('vencedor_time_letra' = winning team letter)
- **Campeonatos**: Tournaments ('completo' = completed)
- **Times**: Teams ('regiao' = region)

**Technical Details:**
- **Emojis**: Attributes like `emoji` and `emoji_discord` follow the Discord format: `<:mibr:1370182490953748490>`.
- **Pickban Log**: Formatted as JSON: `{ "Abans": [12, 2], "Bbans": [7, 9], "Apicks": [5], "Bpicks": [4], "decider": 1 }`, where numbers refer to `mapas_lista.id`.
- **Team References**: `atk_str`, `vencedor_mapa`, and `vencedor_time_letra` use 'A' or 'B' values.
- **Round History**: `rounds_string` resembles `BBBBABBBABBBXAABAAAABAB`. 'A'/'B' indicates the winner of that round; 'X' at position 13 marks half-time, and at position 26 marks overtime.
- **Percentage-based attributes**: Stored as decimals (e.g., `0.55` for 55%). Examples are HS and KAST.

---

## Environment Variables (.env)

- `DISCORD_TOKEN`: Your Discord bot token.
- `DATABASE_URL`: Your PostgreSQL connection string.
- `GUILD_ID`: Server ID for testing (remove `guild=...` from commands to sync globally, though this is slower).
- `CREATOR_ID`: Your Discord ID (restricts RAM cache updates to the owner).

---

## How to Run
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Set up the Database (see [QuickBuild](#quickbuild-of-database)).
4. Create a `.env` file with your credentials (rename [.env.example](.env.example) and fill it in).
5. Run `python src/auto_scrapper.py` to populate your database.
6. Run `python src/main.py` to start the bot.

---

### QuickBuild of Database
To replicate the database on Neon Tech:
1. Access [Neon Tech Console](https://console.neon.tech/).
2. Create a new project.
3. Open the **SQL Editor**.
4. Copy and execute the SQL script provided below to generate the tables and foreign keys.
```
CREATE TABLE "agentes" (
  "id" integer PRIMARY KEY,
  "nome" text,
  "emoji_discord" text
);

CREATE TABLE "campeonatos" (
  "id" integer PRIMARY KEY,
  "nome" text,
  "url" text,
  "completo" boolean
);

CREATE TABLE "composicoes" (
  "id" integer PRIMARY KEY,
  "agente1" integer,
  "agente2" integer,
  "agente3" integer,
  "agente4" integer,
  "agente5" integer
);

CREATE TABLE "mapas_lista" (
  "id" integer PRIMARY KEY,
  "nome" text,
  "in_pool" boolean
);

CREATE TABLE "times" (
  "id" integer PRIMARY KEY,
  "nome" text,
  "tag" text,
  "regiao" text,
  "emoji" text,
  "img_url" text
);

CREATE TABLE "mapas_jogados" (
  "id" integer PRIMARY KEY,
  "partida_id" integer,
  "mapa_id" integer,
  "atk_str" char(1),
  "compa_id" integer,
  "compb_id" integer,
  "rounds_string" text,
  "vencedor_mapa" char(1)
);

CREATE TABLE "partidas" (
  "id" integer PRIMARY KEY,
  "timea_id" integer,
  "timeb_id" integer,
  "pickban_log" text,
  "vencedor_time_letra" char(1),
  "camp_id" integer
);

CREATE TABLE "players" (
  "id" integer PRIMARY KEY,
  "nome" text
);

CREATE TABLE "stats_players" (
  "id_player" integer,
  "id_time" integer,
  "id_camp" integer,
  "rating" numeric(3,2),
  "acs" numeric(4,1),
  "kd" numeric(3,2),
  "kast" numeric(3,2),
  "adr" numeric(4,1),
  "kpr" numeric(3,2),
  "apr" numeric(3,2),
  "fkpr" numeric(3,2),
  "fdpr" numeric(3,2),
  "hs" numeric(3,2),
  "cl" text,
  PRIMARY KEY ("id_player", "id_time", "id_camp")
);

ALTER TABLE "composicoes" ADD FOREIGN KEY ("agente1") REFERENCES "agentes" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "composicoes" ADD FOREIGN KEY ("agente2") REFERENCES "agentes" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "composicoes" ADD FOREIGN KEY ("agente3") REFERENCES "agentes" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "composicoes" ADD FOREIGN KEY ("agente4") REFERENCES "agentes" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "composicoes" ADD FOREIGN KEY ("agente5") REFERENCES "agentes" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "mapas_jogados" ADD FOREIGN KEY ("compa_id") REFERENCES "composicoes" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "mapas_jogados" ADD FOREIGN KEY ("compb_id") REFERENCES "composicoes" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "mapas_jogados" ADD FOREIGN KEY ("mapa_id") REFERENCES "mapas_lista" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "mapas_jogados" ADD FOREIGN KEY ("partida_id") REFERENCES "partidas" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "partidas" ADD FOREIGN KEY ("timea_id") REFERENCES "times" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "partidas" ADD FOREIGN KEY ("timeb_id") REFERENCES "times" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "partidas" ADD FOREIGN KEY ("camp_id") REFERENCES "campeonatos" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "stats_players" ADD FOREIGN KEY ("id_player") REFERENCES "players" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "stats_players" ADD FOREIGN KEY ("id_time") REFERENCES "times" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "stats_players" ADD FOREIGN KEY ("id_camp") REFERENCES "campeonatos" ("id") DEFERRABLE INITIALLY IMMEDIATE;
```
5. Copy your connection string from the dashboard. 
   *Note: Ensure `sslmode=require` is present in the URL.*
6. **Manual Data Seeding:** Some tables do not auto-populate in this version. You should checkout the `discBot_prototype` branch and use `migrar.ipynb` to populate the `times`, `mapas_lista`, and `agentes` tables. Note that some records (like `campeonatos`) must be added manually. You will also need to manually update these tables when new maps or agents are released, or when the map pool changes.