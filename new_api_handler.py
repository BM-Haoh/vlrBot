import json
import os

DIRETORIO_DADOS = os.path.join("BotAPP", "botAPI")
ARQUIVO_INDICE= "indice.json"

def carregar_indice(IND = ARQUIVO_INDICE):
    caminho_arquivo = os.path.join(DIRETORIO_DADOS, IND)
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        print("ERRO INDICE")                                                        # EXCLUIR
        return {}

def get_dados(indice, chave):
    info = indice.get(chave)

    if info:
        caminho_arquivo = os.path.join(DIRETORIO_DADOS, info.get("path"))
        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except FileNotFoundError:
            print("ERRO DADOS")                                                     # EXCLUIR
            return None
    print("ERRO INFO")                                                              # EXCLUIR
    return None

class handler():
    
    def __init__(self, json):
        self.json = json
        self.indice = carregar_indice()
        self.agentes = get_dados(self.indice, "agents")
        self.mapas = get_dados(self.indice, "mapas")
        self.times = get_dados(self.indice, "times")
        self.partidas = get_dados(self.indice, "partidas")
        if (not self.agentes) or (not self.mapas) or (not self.times) or (not self.partidas):
            print("Error")
            return ""

    def add_partidas(self):
        for partida in self.json:
            self.__add_partida(partida)

    def __add_partida(self, partida):
        if self.times:

            for time in self.times:
                if partida.get("times")[0] in (time.get("nome").upper(), time.get("tag").upper()):
                    partida["times"][0] = time.get("TIME_ID")
                    
                    self.times[time.get("TIME_ID") - 1]["partidas"].append(self.partidas[-1].get("id") + 1)

                if partida.get("times")[1] in (time.get("nome").upper(), time.get("tag").upper()):
                    partida["times"][1] = time.get("TIME_ID")
                    
                    self.times[time.get("TIME_ID") - 1]["partidas"].append(self.partidas[-1].get("id") + 1)


            if type(partida["times"][0]) != int or type(partida["times"][1]) != int:
                return f"Algum dos times não foi encontrado."
            
            

            #   TROCANDO NOME DE AGENTE POR ID
            comp1 = [[], [], [] , [], []]
            comp2 = [[], [], [] , [], []]


            for i in range(len(partida.get("mapas"))):
                for agente in self.agentes:
                    if agente.get("nome") in partida.get("mapas")[i].get('composicoes')[0]:
                        comp1[i].append(agente.get("id"))
                    if agente.get("nome") in partida.get("mapas")[i].get('composicoes')[1]:
                        comp2[i].append(agente.get("id"))

                partida["mapas"][i]["composicoes"][0] = comp1[i]
                partida["mapas"][i]["composicoes"][1] = comp2[i]

            #   TROCANDO NOME DE MAPA POR ID

            for mapa in self.mapas:
                for i in range(len(partida.get("mapas"))):
                    #   ID DE CADA MAPA JOGADO
                    if str(partida.get("mapas")[i].get("id")).lower() == mapa.get("nome").lower():
                        partida["mapas"][i]["id"] = mapa.get("id")
                
                #   ID DOS BANS DE A
                for i, choosed_map in enumerate(partida.get("pickban").get("Abans")):
                    if choosed_map == mapa.get("nome"):
                        partida["pickban"]["Abans"][i] = mapa.get("id")
                #   ID DOS BANS DE B
                for i, choosed_map in enumerate(partida.get("pickban").get("Bbans")):
                    if choosed_map == mapa.get("nome"):
                        partida["pickban"]["Bbans"][i] = mapa.get("id")
                #   ID DOS PICKS DE A
                for i, choosed_map in enumerate(partida.get("pickban").get("Apicks")):
                    if choosed_map == mapa.get("nome"):
                        partida["pickban"]["Apicks"][i] = mapa.get("id")
                #   ID DOS PICKS DE A
                for i, choosed_map in enumerate(partida.get("pickban").get("Bpicks")):
                    if choosed_map == mapa.get("nome"):
                        partida["pickban"]["Bpicks"][i] = mapa.get("id")
                #   ID DO DECIDER
                if partida.get("pickban").get("decider") == mapa.get("nome"):
                    partida["pickban"]["decider"] = mapa.get("id")

            self.partidas.append(
                {
                    "id": self.partidas[-1]["id"] + 1,
                    "camp": partida.get("camp"),
                    "timeA/B": partida.get("times"),
                    "mapas": partida.get("mapas"),
                    "pickban": partida.get("pickban"),
                    "win": partida.get("winner")
                }
            )

            with open(os.path.join(DIRETORIO_DADOS, self.indice.get("partidas").get("path")), "w", encoding="utf-8") as arquivo:
                json.dump(self.partidas, arquivo, indent=4, ensure_ascii=False)

            with open(os.path.join(DIRETORIO_DADOS, self.indice.get("times").get("path")), "w", encoding="utf-8") as arquivo:
                json.dump(self.times, arquivo, indent=4, ensure_ascii=False)

            return 0
            
        else:
            return f"Erro ao carregar os times."
        
if __name__ == "__main__":
    indice = carregar_indice()
    print(indice.get("mapas").get("pool"))