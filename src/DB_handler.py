import os
import json
import psycopg
from dotenv import load_dotenv



load_dotenv()
class DB_handler:
    def __init__(self, matches):
        self.DB_URL = os.getenv("DATABASE_URL")
        self.matches = matches

        self.map_dict = self.__load_id_maps()
        self.agent_dict = self.__load_id_agents()
        self.teams_dict = self.__load_id_times()

    def process_matches(self):
        try:
            with self.__get_conn() as conn:
                with conn.cursor() as cur:
                    for p in self.matches:
                        # Mapeamento: timeA/B é uma lista [ID_A, ID_B]
                        id_partida = p['id']
                        id_time_a = self.teams_dict.get(p['times'][0])
                        id_time_b = self.teams_dict.get(p['times'][1])

                        # Convertendo o dicionário de pickban para string JSON
                        pb = p["pickban"]

                        # Processando bans
                        if  pb.get("Abans"):
                            pb["Abans"] = [self.map_dict[m.lower().strip()] for m in pb["Abans"]]
                        if  pb.get("Bbans"):
                            pb["Bbans"] = [self.map_dict[m.lower().strip()] for m in pb["Bbans"]]
                        # Processando picks
                        pb["Apicks"] = [self.map_dict[m.lower().strip()] for m in pb["Apicks"]]
                        pb["Bpicks"] = [self.map_dict[m.lower().strip()] for m in pb["Bpicks"]]

                        # Processando decider
                        pb["decider"] = self.map_dict[pb.get("decider").lower().strip()]

                        pickban_str = json.dumps(p['pickban'])

                        # 1. Inserir/Atualizar a Partida
                        cur.execute("""
                            INSERT INTO partidas (id, camp_id, timeA_id, timeB_id, pickban_log, vencedor_time_letra)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET 
                                camp_id = EXCLUDED.camp_id,
                                vencedor_time_letra = EXCLUDED.vencedor_time_letra;
                        """, (id_partida, p['camp'], id_time_a, id_time_b, pickban_str, p['winner']))

                        # 2. Processar a lista de mapas (MD3 ou MD5)
                        for mapa in p['mapas']:
   
                            # No seu JSON: composicoes[0] é o Time A, composicoes[1] é o Time B
                            id_comp_a = self.__get_or_create_comp(mapa['composicoes'][0])
                            id_comp_b = self.__get_or_create_comp(mapa['composicoes'][1])

                            id_mapa = self.map_dict.get(mapa['nome'].lower().strip())
                            # 3. Inserir o Mapa jogado, associando à partida e às composições
                            # Note: 'atk' no seu JSON vira 'atk_start' no banco
                            cur.execute("""
                                INSERT INTO mapas_jogados (partida_id, mapa_id, atk_start, compA_id, compB_id, rounds_string, vencedor_mapa)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (id_partida, id_mapa, mapa['atk'], id_comp_a, id_comp_b, mapa['rounds'], mapa['win']))

                    conn.commit()

        except Exception as e:
            print(f"Erro durante a migração: {e}")

    def __load_id_maps(self):
        with self.__get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nome FROM mapas_lista")
                return {nome.lower(): int(id) for id, nome in cur.fetchall()}
            
    def __load_id_agents(self):
        with self.__get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nome FROM agentes_lista")
                return {nome.lower(): int(id) for id, nome in cur.fetchall()}
            
    def __load_id_times(self):
        with self.__get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, tag FROM times_lista")
                return {tag.lower(): int(id) for id, tag in cur.fetchall()}
            
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