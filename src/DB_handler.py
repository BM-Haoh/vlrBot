import os
import json
import psycopg
from dotenv import load_dotenv



load_dotenv()
class DB_handler:
    def __init__(self, matches):
        self.DB_URL = os.getenv("DATABASE_URL")
        self.matches = matches

        self.map_dict, self.agent_dict, self.teams_dict = self.__load_info()

    def process_matches(self):
        #try:
            with self.__get_conn() as conn:
                with conn.cursor() as cur:
                    for p in self.matches:
                        # Mapeamento: timeA/B é uma lista [ID_A, ID_B]
                        id_partida = p['id']
                        id_time_a = self.teams_dict.get(p['times'][0])
                        id_time_b = self.teams_dict.get(p['times'][1])

                        # Convertendo o dicionário de pickban para string JSON
                        pb = {}
                        pool = []
                        map_id = 0

                        map_added = [False, None]
                        # Processando bans
                        if  p.get("Abans"):
                            pool.extend(p["Abans"])
                            for m in p["Abans"]:
                                if m.lower().strip() not in self.map_dict:
                                    map_id = self.__create_map(m.capitalize(), cur)
                                    self.map_dict[m.lower().strip()] = [map_id, True]
                                pb["Abans"] = self.map_dict[m.lower().strip()][0]

                        if  p.get("Bbans"):
                            pool.extend(p["Bbans"])
                            for m in p["Bbans"]:
                                if m.lower().strip() not in self.map_dict:
                                    map_id = self.__create_map(m.capitalize(), cur)
                                    self.map_dict[m.lower().strip()] = [map_id, True]
                            pb["Bbans"] = [self.map_dict[m.lower().strip()][0] for m in p["Bbans"]]

                        # Processando picks
                        pool.extend(p["Apicks"])
                        for m in p["Apicks"]:
                            if m.lower().strip() not in self.map_dict:
                                map_id = self.__create_map(m.capitalize(), cur)
                                self.map_dict[m.lower().strip()] = [map_id, True]
                        pb["Apicks"] = [self.map_dict[m.lower().strip()][0] for m in p["Apicks"]]

                        pool.extend(p["Bpicks"])
                        for m in p["Bpicks"]:
                            if m.lower().strip() not in self.map_dict:
                                map_id = self.__create_map(m.capitalize(), cur)
                                self.map_dict[m.lower().strip()] = [map_id, True]
                        pb["Bpicks"] = [self.map_dict[m.lower().strip()][0] for m in p["Bpicks"]]


                        # Processando decider
                        m = p["decider"]
                        pool.append(m)
                        if m.lower().strip() not in self.map_dict:
                            map_id = self.__create_map(m.capitalize(), cur)
                            self.map_dict[m.lower().strip()] = [map_id, True]
                        pb["decider"] = self.map_dict[m.lower().strip()][0]

                        pickban_str = json.dumps(p['pickban'])

                        pool_change = False
                        for map in pool:
                            if not self.map_dict[map.lower().strip()][1]:
                                pool_change = True
                                break

                        if map_id:
                            pool_change = True

                        if pool_change:
                            pool_id = []
                            for map in self.map_dict:
                                self.map_dict[map][1] = False
                            for i, map in enumerate(pool):
                                self.map_dict[map.lower().strip()][1] = True
                                pool_id.append(self.map_dict[map.lower().strip()][0])

                            cur.execute("""
                                UPDATE mapas_lista SET in_pool = FALSE
                                        """)
                            cur.execute("""
                                UPDATE mapas_lista SET in_pool = TRUE
                                WHERE id = ANY(%s)""", (pool_id,))
                        
                        # 1. Inserir/Atualizar a Partida
                        cur.execute("""
                            INSERT INTO partidas (id, camp_id, timea_id, timeb_id, pickban_log, vencedor_time_letra)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET 
                                camp_id = EXCLUDED.camp_id,
                                vencedor_time_letra = EXCLUDED.vencedor_time_letra;
                        """, (id_partida, p['camp'], id_time_a, id_time_b, pickban_str, p['winner']))

                        # 2. Processar a lista de mapas (MD3 ou MD5)
                        for mapa in p['mapas']:
   
                            # No seu JSON: composicoes[0] é o Time A, composicoes[1] é o Time B
                            id_comp_a = self.__get_or_create_comp(mapa['composicoes'][0], cur)
                            id_comp_b = self.__get_or_create_comp(mapa['composicoes'][1], cur)

                            id_mapa = self.map_dict.get(mapa['id'].lower().strip())
                            # 3. Inserir o Mapa jogado, associando à partida e às composições
                            # Note: 'atk' no seu JSON vira 'atk_start' no banco
                            cur.execute("""
                                INSERT INTO mapas_jogados (partida_id, mapa_id, atk_start, compA_id, compB_id, rounds_string, vencedor_mapa)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (id_partida, id_mapa, mapa['atk'], id_comp_a, id_comp_b, mapa['rounds'], mapa['win']))

                    conn.commit()

        # except Exception as e:
        #     print(f"Erro durante a migração: {e}")

    def __load_id_maps(self, cur):
        cur.execute("SELECT id, nome, in_pool FROM mapas_lista")
        return {nome.lower(): [int(id), in_pool] for id, nome, in_pool in cur.fetchall()}
            
    def __load_id_agents(self, cur):
        cur.execute("SELECT id, nome FROM agentes")
        return {nome.lower(): int(id) for id, nome in cur.fetchall()}
            
    def __load_id_times(self, cur):
        cur.execute("SELECT id, tag FROM times")
        return {tag: int(id) for id, tag in cur.fetchall()}
    
    def __load_info(self):
        with self.__get_conn() as conn:
            with conn.cursor() as cur:
                return self.__load_id_maps(cur), self.__load_id_agents(cur), self.__load_id_times(cur)
            
    def __create_map(self, map_name, cur):
        cur.execute("""
            INSERT INTO mapas_lista (nome, in_pool) VALUES (%s, %s) RETURNING id
        """, (map_name, True))
        return cur.fetchone()[0]

            
    def __get_or_create_comp(self, agents_names, cur):
        agents_ids = [self.agent_dict.get(name.lower().strip()) for name in agents_names]
        agents_ids.sort()  # Ordena os IDs para garantir a consistência na busca
        
        cur.execute("""
            SELECT id FROM composicoes 
            WHERE agente1=%s AND agente2=%s AND agente3=%s AND agente4=%s AND agente5=%s
        """, agents_ids)
        res = cur.fetchone()
        
        if res:
            return res[0]
        else:
            cur.execute("""
                INSERT INTO composicoes (agente1, agente2, agente3, agente4, agente5)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, agents_ids)
            return cur.fetchone()[0]

    def __get_conn(self):
        return psycopg.connect(self.DB_URL)