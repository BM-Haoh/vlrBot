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
