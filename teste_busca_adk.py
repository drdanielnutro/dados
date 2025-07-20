import os
import sys
import json
import unicodedata
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI

# =====================================================================
# COMO FORMATAR A STRING DE BUSCA PARA O ADK
# =====================================================================
# 
# A string de busca deve, preferencialmente, começar com "adk" para 
# melhor contextualização. Esta é uma ORIENTAÇÃO, não uma obrigação.
#
# FORMATO RECOMENDADO:
# "adk [classe] [método] [descrição da dúvida]"
#
# EXEMPLOS:
# - "adk MainActivity onCreate como inicializar"
# - "adk Fragment onCreateView inflar layout"
# - "adk RecyclerView Adapter notifyDataSetChanged"
# - "adk erro NullPointerException lista vazia"
# - "adk AsyncTask doInBackground thread"
#
# FORMATOS ACEITOS PELO SISTEMA:
# 1. Com ponto e vírgula: "categoria;consulta"
#    Exemplo: "erroClasse;stack trace NullPointer"
#
# 2. Com espaço: "categoria consulta"
#    Exemplo: "activity como criar nova tela"
#    (A primeira palavra será usada como filtro/categoria)
#
# =====================================================================

# ---------------------------------------------------------------------
# Carrega OPENAI_API_KEY do .env  (OPENAI_API_KEY="sk-sua-chave-aqui")
# ---------------------------------------------------------------------
load_dotenv()

# ------------------------ CONFIGURAÇÕES ------------------------------
MONGO_USER       = "deniellmed"
MONGO_PASS       = "Wm2208201003"
MONGO_DB         = "buildShild"
MONGO_COLLECTION = "adk"
MONGO_URI        = (
    f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}"
    "@cluster0.icwdtnz.mongodb.net/?retryWrites=true&w=majority"
)

VECTOR_INDEX_NAME = "adk_index"
VECTOR_FIELD_PATH = "descricao_embedding"   # campo vetorial
MIN_SCORE_THRESHOLD = float(os.getenv("MIN_SCORE_THRESHOLD", "0.7"))   # Score mínimo (padrão: 0.7)
MAX_RESULTS_TO_FETCH = int(os.getenv("MAX_RESULTS_TO_FETCH", "10"))   # Número de documentos a buscar (padrão: 10)

# ---------------------------------------------------------------------
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------- FUNÇÕES -----------------------------------
def normalize(text: str) -> str:
    """Remove acentuação e deixa tudo minúsculo."""
    nfkd = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()

def get_embedding(text: str) -> list[float]:
    """Chama a OpenAI e devolve o vetor embedding."""
    print(f"Gerando embedding para: '{text}' …")
    resp = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    )
    print("Embedding gerado!")
    return resp.data[0].embedding

def build_filter(category_raw: str) -> dict:
    """
    Constrói o filtro a partir do trecho antes do ';'
    Ex.: 'erroClasse;stack'  ➜ category_raw = 'erroClasse'
    """
    category = normalize(category_raw)
    return {
        "$or": [
            {"filtro":   category},
            {"filtro_2": category}
        ]
    }

def execute_vector_search(query_vector: list[float], filter_dict: dict = None) -> list:
    """Executa busca vetorial com ou sem filtro."""
    pipeline = []
    
    # Estágio de busca vetorial
    vector_search_stage = {
        "$vectorSearch": {
            "index": VECTOR_INDEX_NAME,
            "path":  VECTOR_FIELD_PATH,
            "queryVector": query_vector,
            "numCandidates": 100,
            "limit": MAX_RESULTS_TO_FETCH
        }
    }
    
    # Adiciona filtro se fornecido
    if filter_dict:
        vector_search_stage["$vectorSearch"]["filter"] = filter_dict
    
    pipeline.append(vector_search_stage)
    
    # Adiciona score
    pipeline.extend([
        {
            "$addFields": {
                "searchScore": {"$meta": "vectorSearchScore"}
            }
        },
        {
            "$match": {
                "searchScore": {"$gte": MIN_SCORE_THRESHOLD}
            }
        },
        {
            "$project": {
                "descricao_embedding": 0  # Exclui o campo descricao_embedding
            }
        }
    ])
    
    try:
        client = MongoClient(MONGO_URI)
        coll = client[MONGO_DB][MONGO_COLLECTION]
        docs = list(coll.aggregate(pipeline))
        client.close()
        return docs
    except Exception as e:
        print(f"Falha na consulta MongoDB: {e}")
        return []

def search_document(query: str):
    """
    Busca vetorial com filtro nos campos filtro / filtro_2, com fallback sem filtro.
    
    FORMATOS DE ENTRADA ACEITOS:
    1. Com ponto e vírgula: "categoria;descrição"
       - Exemplo: "activity;como criar uma nova activity"
       - A parte antes do ';' é usada como filtro
       - A query completa é usada para busca vetorial
    
    2. Com espaço: "categoria descrição"
       - Exemplo: "fragment lifecycle onResume"
       - A primeira palavra é usada como filtro
       - O restante é usado para busca vetorial
    
    RECOMENDAÇÃO: Inicie com "adk" para melhor contexto
       - Exemplo: "adk activity onCreate savedInstanceState"
    """
    print("-" * 50)
    print(f"Consulta recebida: '{query}'")

    # --- PROCESSAMENTO DA STRING DE BUSCA ---
    # O sistema aceita dois formatos de entrada:
    # 1. "categoria;consulta" - usa ponto e vírgula como separador
    # 2. "categoria consulta" - usa espaço como separador
    if ";" in query:
        # FORMATO 1: Mantém compatibilidade com ponto e vírgula
        # Ex: "activity;como criar nova tela" -> filtro="activity", busca="activity como criar nova tela"
        category_raw, extra = query.split(";", 1)
        full_query = f"{category_raw.strip()} {extra.strip()}"
    else:
        # FORMATO 2: Nova lógica - primeira palavra é o filtro
        # Ex: "fragment onCreateView inflar" -> filtro="fragment", busca="onCreateView inflar"
        parts = query.split(" ", 1)
        if len(parts) > 1:
            category_raw = parts[0]
            extra = parts[1]
            full_query = extra  # Busca apenas pelo resto da query (sem o filtro)
            print(f"Filtro detectado: '{category_raw}'")
            print(f"Query de busca: '{full_query}'")
        else:
            # Query de uma palavra só - usa a palavra tanto como filtro quanto busca
            # Ex: "activity" -> filtro="activity", busca="activity"
            category_raw = query
            full_query = query

    try:
        query_vector = get_embedding(full_query)
    except Exception as e:
        print(f"Erro no embedding: {e}")
        return None

    # Primeira tentativa: COM filtro
    # O filtro é aplicado nos campos "filtro" e "filtro_2" do MongoDB
    # Isso permite buscar documentos específicos de uma categoria
    print("Executando busca vetorial com filtro …")
    filter_dict = build_filter(category_raw)
    docs = execute_vector_search(query_vector, filter_dict)
    
    if docs:
        print(f"Encontrados {len(docs)} documentos com filtro.")
        # Ordenar por score decrescente e pegar o melhor
        best_doc = max(docs, key=lambda d: d.get('searchScore', 0))
        best_doc["_busca_com_filtro"] = True
        print(f"Retornando documento com maior score: {best_doc.get('searchScore', 'N/A')}")
        print("Conexão MongoDB encerrada.")
        print("-" * 50)
        return best_doc
    
    # Fallback: SEM filtro
    # Se não encontrar resultados com o filtro de categoria, faz busca geral
    # Isso garante que sempre retorne algo relevante, mesmo sem categoria exata
    print("Nenhum resultado com filtro. Tentando busca sem filtro…")
    docs = execute_vector_search(query_vector, filter_dict=None)
    
    if docs:
        print(f"Encontrados {len(docs)} documentos SEM filtro (fallback).")
        # Ordenar por score decrescente e pegar o melhor
        best_doc = max(docs, key=lambda d: d.get('searchScore', 0))
        best_doc["_busca_com_filtro"] = False
        print(f"Retornando documento com maior score: {best_doc.get('searchScore', 'N/A')}")
        print("Conexão MongoDB encerrada.")
        print("-" * 50)
        return best_doc
    
    print("Nenhum documento encontrado mesmo sem filtro.")
    print("Conexão MongoDB encerrada.")
    print("-" * 50)
    return None

# ----------------------------- MAIN ----------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:  python busca_adk.py \"sua consulta aqui\"")
        print("\nExemplos de uso:")
        print('  python busca_adk.py "adk activity onCreate"')
        print('  python busca_adk.py "fragment;como usar onCreateView"')
        print('  python busca_adk.py "recyclerview adapter notifyDataSetChanged"')
        sys.exit(1)

    consulta = sys.argv[1]
    doc = search_document(consulta)

    if doc:
        print("\n--- DOCUMENTO ENCONTRADO ---")
        print(f"Score: {doc.get('searchScore', 'N/A')}")
        if doc.get("_busca_com_filtro", True):
            print("Tipo de busca: COM filtro")
        else:
            print("Tipo de busca: SEM filtro (fallback)")
        
        # Remove campo interno antes de exibir
        doc.pop("_busca_com_filtro", None)
        print(json.dumps(doc, indent=4, default=str))
    else:
        print(f"\nNenhum documento encontrado com score >= {MIN_SCORE_THRESHOLD}")
