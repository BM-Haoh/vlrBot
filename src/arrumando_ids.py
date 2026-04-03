import json
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

def atualizar_ids_vlr_no_banco():
    # 1. Carrega o novo JSON que tem o mapeamento
    with open(r".\botAPI\new_partidas.json", "r", encoding="utf-8") as f:
        novos_dados = json.load(f) 

    # 2. Conecta ao Neon
    conn = psycopg.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    try:
        print("🔄 Iniciando a tradução de IDs para o padrão VLR.gg...")
        
        for item in novos_dados:
            vlr_id = int(item["new_id"])      # O ID real do VLR (Ex: 456789)
            json_id = item["id"]         # O ID que está no JSON (Ex: 2)
            
            # Localiza o ID que está ATUALMENTE no banco (Ex: 2 - 1 = 1)
            id_atual_no_banco = json_id - 1
            
            # UPDATE: Troca o ID sequencial pelo ID do VLR
            # O CASCADE garante que as Foreign Keys não quebrem
            cur.execute(
                "UPDATE partidas SET id = %s WHERE id = %s",
                (vlr_id, id_atual_no_banco)
            )
            
            if cur.rowcount > 0:
                print(f"✅ Sucesso: Banco({id_atual_no_banco}) agora é VLR({vlr_id})")
            else:
                print(f"⚠️ Aviso: ID {id_atual_no_banco} não encontrado no banco.")

        conn.commit()
        print("\n✨ Processo finalizado! Todos os IDs foram convertidos.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro crítico: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    atualizar_ids_vlr_no_banco()