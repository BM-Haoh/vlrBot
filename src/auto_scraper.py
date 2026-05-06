from auto import tournament_manager
from DB_handler import DB_handler

def run():
    try:
        mtc_grt = tournament_manager()
        matches = mtc_grt.process_camps()
        
        if matches:
            DBH = DB_handler(matches)
            DBH.process_matches()
        else:
            print("Nenhuma partida nova para processar.")
    except Exception as e:
        print(f"Erro na execução: {e}")
        exit(1) # Força o GitHub Actions a marcar como falha se der erro

if __name__ == "__main__":
    run()