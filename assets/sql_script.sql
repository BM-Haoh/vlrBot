CREATE TABLE "agentes" (
  "id" integer PRIMARY KEY,
  "nome" text,
  "emoji_discord" text
);

CREATE TABLE "campeonatos" (
  "id" integer PRIMARY KEY,
  "nome" text,
  "url" text,
  "completo" boolean DEFAULT false,
  "winner" integer,
  "rated" boolean
);

CREATE TABLE "composicoes" (
  "id" integer PRIMARY KEY,
  "agente1" integer NOT NULL,
  "agente2" integer NOT NULL,
  "agente3" integer NOT NULL,
  "agente4" integer NOT NULL,
  "agente5" integer NOT NULL
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
  "partida_id" integer NOT NULL,
  "mapa_id" integer NOT NULL,
  "atk_str" char(1),
  "compa_id" integer NOT NULL,
  "compb_id" integer NOT NULL,
  "rounds_string" text,
  "vencedor_mapa" char(1)
);

CREATE TABLE "partidas" (
  "id" integer PRIMARY KEY,
  "timea_id" integer NOT NULL,
  "timeb_id" integer NOT NULL,
  "pickban_log" text,
  "vencedor_time_letra" char(1),
  "camp_id" integer NOT NULL,
  "rated" boolean NOT NULL DEFAULT false,
  "seq_num" integer
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
  "hs" numeric(3,2),
  "cl" text,
  "fkfd" numeric(4,2),
  PRIMARY KEY ("id_player", "id_time", "id_camp")
);

CREATE TABLE "players_map_stats" (
  "player_id" integer,
  "match_id" integer,
  "map_id" integer,
  "team_id" integer,
  "rating" numeric(4,2),
  "acs" integer,
  "adr" integer,
  "kast" numeric(4,2),
  "hs" numeric(4,2),
  "kd" numeric(5,2),
  "kda" numeric(5,2),
  "fk" integer,
  "fd" integer,
  PRIMARY KEY ("player_id", "match_id", "map_id", "team_id")
);

CREATE TABLE "team_ratings" (
  "team_id" integer,
  "map_id" integer,
  "rating" integer DEFAULT 1000,
  "pickpoints" integer DEFAULT 0,
  PRIMARY KEY ("team_id", "map_id")
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

ALTER TABLE "campeonatos" ADD FOREIGN KEY ("winner") REFERENCES "times" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "players" ADD FOREIGN KEY ("id") REFERENCES "stats_players" ("id_player") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "times" ADD FOREIGN KEY ("id") REFERENCES "stats_players" ("id_time") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "campeonatos" ADD FOREIGN KEY ("id") REFERENCES "stats_players" ("id_camp") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "times" ADD FOREIGN KEY ("id") REFERENCES "team_ratings" ("team_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "mapas_lista" ADD FOREIGN KEY ("id") REFERENCES "team_ratings" ("map_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "players" ADD FOREIGN KEY ("id") REFERENCES "players_map_stats" ("player_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "partidas" ADD FOREIGN KEY ("id") REFERENCES "players_map_stats" ("match_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "mapas_lista" ADD FOREIGN KEY ("id") REFERENCES "players_map_stats" ("map_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "times" ADD FOREIGN KEY ("id") REFERENCES "players_map_stats" ("team_id") DEFERRABLE INITIALLY IMMEDIATE;
