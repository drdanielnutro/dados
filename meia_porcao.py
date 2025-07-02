
# Script Python para Classificação de Porções de Alimentos
# Adaptado de: script de otimização de prompts de ativos
# Missão: Analisar um JSON de alimento e determinar se "meia porção" é culturalmente aceitável.

import json
import os
import logging
import asyncio
import argparse
import re
import sys
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Dict, Any, List
import anthropic

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("classificacao_porcoes.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Configura a chave de API do Anthropic
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    logger.critical("A variável de ambiente ANTHROPIC_API_KEY não foi encontrada.")
    sys.exit("Erro: Chave de API da Anthropic não configurada.")

# Inicializa o cliente Anthropic
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

# --- [MODIFICAÇÃO 1] Definição do Modelo Pydantic para Alimento ---
class FoodDocument(BaseModel):
    id: int  # ID numérico como identificador único
    nome_cardapio: str
    unidadeCaseira: str = Field(..., alias='unidadeCaseira')

# --- [MODIFICAÇÃO 2] System Instructions do Avaliador de Porções ---
system_instructions = """
## INSTRUÇÃO DE SISTEMA - AVALIADOR DE PORÇÕES CULINÁRIAS (v2.0)

### 1. IDENTIDADE E OBJETIVO
**SYSTEM_CONTEXT:**
Você é um **Avaliador de Porções Culinárias**, um assistente de IA especialista em lógica de cardápios e práticas de consumo no contexto brasileiro. Sua função é analisar dados de alimentos, um por um, e determinar com base em critérios culturais e práticos se a oferta de "meia porção" para aquele item específico faz sentido. Seu objetivo principal é funcionar como um classificador preciso, cuja decisão (`true` ou `false`) habilitará ou não um cálculo subsequente de divisão de valores nutricionais. Sua análise não se baseia apenas no alimento, mas na **combinação crítica entre o alimento e sua unidade de medida**.

### 2. CONTEXTO DA TAREFA
**TASK_CONTEXT:**
Você receberá, a cada chamada, um único documento JSON representando um alimento. Sua tarefa é analisar dois campos específicos deste JSON: `nome_cardapio` e `unidade_caseira`. Sua única saída deve ser um objeto JSON válido, contendo exclusivamente a chave `aceita_meia_porcao` com um valor booleano (`true` ou `false`).
**Exemplo de Saída Válida:**
```json
{
  "aceita_meia_porcao": true
}
```

### 3. LÓGICA DE DECISÃO E CRITÉRIOS (BASEADO EM GUIA BRASILEIRO)
**DECISION_LOGIC:**
O princípio fundamental da sua análise é: **A divisão da `unidade_caseira` por dois resulta em uma quantidade que uma pessoa comum no Brasil consideraria prática, reconhecível e aceitável para consumir?** Para tomar sua decisão, aplique os seguintes princípios e use a tabela de raciocínio como seu guia principal.

#### **Princípios de Decisão:**
1.  **Princípio da Divisibilidade (Geralmente `true`):** Itens grandes, fracionáveis, ou servidos a partir de uma fonte maior (ex: uma travessa) geralmente aceitam meia porção.
2.  **Princípio da Unidade Mínima (Geralmente `false`):** Itens pequenos, consumidos como uma unidade única, ou embalados individualmente, geralmente NÃO aceitam meia porção.
3.  **Princípio da Praticidade (Fator Decisivo):** A "meia porção" resultante é fácil de medir e servir?

#### **Tabela de Raciocínio Estratégico:**
| `nome_cardapio` | `unidade_caseira` | Decisão | Raciocínio Chave (Seu pensamento interno) |
| :--- | :--- | :--- | :--- |
| Pão francês | Unidade | `true` | Princípio da Divisibilidade. É culturalmente comum cortar ao meio. |
| Ovo cozido | Unidade | `false` | Princípio da Unidade Mínima. É um item pequeno, consumido inteiro. |
| Mamão Formosa | Fatia | `true` | Princípio da Divisibilidade. "Meia fatia" é uma porção normal. |
| Mamão picado | Colher de sopa | `false` | Princípio da Praticidade. "Meia colher de sopa" é impraticável. |
| Iogurte | Pote 1L | `true` | Princípio da Divisibilidade. A pessoa serve a quantidade que quer. |
| Iogurte | Pote 170g | `false` | Princípio da Unidade Mínima. É uma embalagem individual. |
| Pizza | Fatia | `true` | Princípio da Divisibilidade. A fatia pode ser grande e dividida. |
| Biscoito recheado | Unidade | `false` | Princípio da Unidade Mínima. Item pequeno e unitário. |

### 4. PROCESSO PASSO A PASSO
1.  Analisar o Input.
2.  Identificar Campos Críticos: `nome_cardapio` e `unidade_caseira`.
3.  Aplicar Raciocínio Crítico.
4.  Tomar a Decisão Booleana.
5.  Formatar a Saída: Construa e retorne o objeto JSON final, e nada mais.

### 5. REGRAS E RESTRIÇÕES
- **NÃO** retorne texto, explicações ou qualquer outra coisa além do objeto JSON especificado.
- **NÃO** baseie sua decisão apenas no `nome_cardapio`. A `unidade_caseira` é o fator decisivo.
- Se a `unidade_caseira` for ambígua, ausente ou não fizer sentido (ex: "gramas"), retorne `false` como medida de segurança.
- Sua análise deve ser determinística e consistente. O mesmo input deve sempre gerar o mesmo output.
"""

# --- Funções de controle de IDs processados (mantidas, mas com nomes mais claros) ---
def read_processed_ids_sync(ids_file: str) -> set:
    try:
        with open(ids_file, "r", encoding="utf-8") as f:
            ids = set(f.read().splitlines())
    except FileNotFoundError:
        ids = set()
    return ids

def append_processed_id_sync(doc_id: str, ids_file: str):
    with open(ids_file, "a", encoding="utf-8") as f:
        f.write(f"{doc_id}\n")

# --- [MODIFICAÇÃO 3] Função de Caminho de Saída ---
def get_next_output_path():
    directory = "dados/resultados_meia_porcao"
    if not os.path.exists(directory):
        os.makedirs(directory)
    files = os.listdir(directory)
    seqs = []
    pattern = re.compile(r"classificacao_porcoes_(\d+)\.json")
    for filename in files:
        match = pattern.match(filename)
        if match:
            seqs.append(int(match.group(1)))
    next_num = max(seqs) + 1 if seqs else 1
    return os.path.join(directory, f"classificacao_porcoes_{next_num}.json")

# --- [MODIFICAÇÃO 4] Função de Preparação de Input ---
def preparar_input_para_api(doc: FoodDocument) -> str:
    """Prepara um JSON simples com os campos que a IA precisa analisar."""
    input_data = {
        "nome_cardapio": doc.nome_cardapio,
        "unidade_caseira": doc.unidadeCaseira
    }
    return json.dumps(input_data, ensure_ascii=False, indent=2)

# --- Função de Retry (mantida) ---
async def retry_async(coro, retries=3, delay=1, factor=2):
    # ... (código original mantido, é robusto)
    attempt = 0
    last_exception = None
    while attempt < retries:
        try:
            return await coro()
        except Exception as e:
            attempt += 1
            last_exception = e
            if attempt < retries:
                wait_time = delay * (factor ** (attempt - 1))
                logger.warning(f"Tentativa {attempt} falhou com erro: {e}. Retentando em {wait_time} segundos...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Número máximo de tentativas ({retries}) atingido. Último erro: {last_exception}")
                return None
    return None

# --- [MODIFICAÇÃO 5] Função de Chamada à API ---
async def chamada_api_claude(doc: FoodDocument, parametros_api: dict) -> Optional[bool]:
    """Chama a API do Claude e faz o parse da resposta booleana."""
    loop = asyncio.get_event_loop()
    doc_id_log = str(doc.id)  # Usando o ID numérico como string para log

    async def fazer_chamada():
        kwargs = {
            "model": parametros_api.get("claude_model", "claude-sonnet-4-20250514"), # Claude Sonnet 4 - versão mais recente
            "system": system_instructions,
            "messages": [{"role": "user", "content": preparar_input_para_api(doc)}],
            "temperature": parametros_api.get("temperature", 0.0), # 0.0 para máxima consistência
            "max_tokens": parametros_api.get("max_tokens", 50) # Resposta é muito curta
        }
        return await loop.run_in_executor(None, lambda: anthropic_client.messages.create(**kwargs))

    try:
        response = await fazer_chamada()
        if hasattr(response, 'usage'):
            logger.debug(f"Alimento ID {doc_id_log} - Tokens: In={response.usage.input_tokens}, Out={response.usage.output_tokens}")

        if response.content and response.content[0].type == 'text':
            texto_resposta = response.content[0].text
            try:
                resultado_json = json.loads(texto_resposta)
                if isinstance(resultado_json, dict) and 'aceita_meia_porcao' in resultado_json:
                    return resultado_json['aceita_meia_porcao']
                else:
                    logger.warning(f"Alimento ID {doc_id_log} - JSON retornado não tem a chave 'aceita_meia_porcao': {texto_resposta}")
                    return None
            except json.JSONDecodeError:
                logger.warning(f"Alimento ID {doc_id_log} - Resposta não é um JSON válido: '{texto_resposta}'")
                return None
        else:
            logger.warning(f"Alimento ID {doc_id_log} - Sem conteúdo na resposta da API")
            return None
    except Exception as e:
        logger.error(f"Alimento ID {doc_id_log} - Erro na chamada à API: {e}")
        return None

# --- [MODIFICAÇÃO 6] Função de Processamento de Item ---
async def processar_item(alimento_data: dict, parametros_api: dict, ids_file: str):
    try:
        doc = FoodDocument(**alimento_data)
        doc_id_log = str(doc.id)  # Usando o ID numérico como string
    except ValidationError as e:
        logger.error(f"Erro de validação para o alimento ID: {alimento_data.get('id', 'ID_DESCONHECIDO')}. Erro: {e}")
        return None

    processed_ids = await asyncio.to_thread(read_processed_ids_sync, ids_file)
    if doc_id_log in processed_ids:
        logger.info(f"Alimento ID {doc_id_log} já foi analisado. Pulando...")
        return None

    async def chamar_api_wrapper():
        return await chamada_api_claude(doc, parametros_api)

    resultado_booleano = await retry_async(chamar_api_wrapper, retries=3, delay=1, factor=2)

    # Se a API falhar, retornamos None para não salvar um resultado incorreto
    if resultado_booleano is None:
        logger.error(f"Alimento ID {doc_id_log}: Falha ao obter classificação da API após retentativas.")
        return None

    resultado = {
        "id": doc.id,
        "nome_cardapio": doc.nome_cardapio,
        "unidadeCaseira": doc.unidadeCaseira,
        "aceita_meia_porcao": resultado_booleano
    }

    logger.info(f"Alimento ID {doc_id_log}: Classificado como 'aceita_meia_porcao' = {resultado_booleano}")
    await asyncio.to_thread(append_processed_id_sync, doc_id_log, ids_file)
    return resultado

# --- [MODIFICAÇÃO 7] Função de Extração de Alimentos ---
def carregar_alimentos(filepath: str) -> List[dict]:
    """Carrega a lista de alimentos de um arquivo JSON."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            logger.info(f"Carregados {len(data)} alimentos do arquivo {filepath}")
            return data
        else:
            logger.error(f"O arquivo {filepath} não contém uma lista JSON na raiz.")
            return []
    except FileNotFoundError:
        logger.error(f"Arquivo de dados não encontrado: {filepath}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON do arquivo: {filepath}")
        return []

# --- [MODIFICAÇÃO 8] Função Principal ---
async def main_async(args):
    all_alimentos = carregar_alimentos(args.input)
    if not all_alimentos:
        return

    logger.info(f"Iniciando classificação de porções de alimentos")

    initial_processed_ids = await asyncio.to_thread(read_processed_ids_sync, args.ids)
    novos_alimentos = [
        alimento for alimento in all_alimentos
        if str(alimento.get('id')) not in initial_processed_ids
    ][:args.max_items]

    logger.info(f"{len(novos_alimentos)} novos alimentos serão analisados")
    if not novos_alimentos:
        logger.info("Nenhum alimento novo para processar.")
        return

    parametros_api = {
        "claude_model": args.claude_model,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }

    semaphore = asyncio.Semaphore(args.max_concurrent)
    async def process_with_semaphore(alimento_data):
        async with semaphore:
            return await processar_item(alimento_data, parametros_api, args.ids)

    tasks = [process_with_semaphore(alimento) for alimento in novos_alimentos]
    results = await asyncio.gather(*tasks)

    valid_results = [r for r in results if r is not None]

    if valid_results:
        total_analisados = len(valid_results)
        total_aceitos = sum(1 for r in valid_results if r['aceita_meia_porcao'])
        
        output_path = get_next_output_path()
        output_data = {
            "total_analisados": total_analisados,
            "total_aceita_meia_porcao_true": total_aceitos,
            "total_aceita_meia_porcao_false": total_analisados - total_aceitos,
            "resultados": valid_results
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Análise concluída. Resultados salvos em {output_path}")
        logger.info(f"Estatísticas: Analisados={total_analisados}, Aceitam Meia Porção={total_aceitos}, Não Aceitam={total_analisados - total_aceitos}")
    else:
        logger.info("Nenhum alimento foi processado com sucesso.")

# --- [MODIFICAÇÃO 9] Configuração de Argumentos CLI ---
def parse_args():
    parser = argparse.ArgumentParser(description="Classifica alimentos quanto à aceitabilidade de 'meia porção' usando a API Claude.")
    parser.add_argument("--input", type=str, default="dados_com_id.json", 
                       help="Arquivo JSON com a lista de alimentos.")
    parser.add_argument("--ids", type=str, default="dados/ids_alimentos_analisados.txt", 
                       help="Arquivo de controle de IDs de alimentos processados.")
    parser.add_argument("--max_items", type=int, default=100, 
                       help="Número máximo de alimentos a processar por execução.")
    parser.add_argument("--max_concurrent", type=int, default=5, 
                       help="Número máximo de requisições concorrentes à API.")
    parser.add_argument("--claude_model", type=str, default="claude-sonnet-4-20250514", 
                       help="Modelo do Claude a usar (Claude Sonnet 4 - versão mais recente).")
    parser.add_argument("--temperature", type=float, default=0.0, 
                       help="Temperature para a API (0.0 para consistência).")
    parser.add_argument("--max_tokens", type=int, default=50, 
                       help="Máximo de tokens para a resposta da IA.")
    return parser.parse_args()

# --- Execução Principal ---
if __name__ == "__main__":
    # Garante que o diretório de dados exista
    if not os.path.exists("dados"):
        os.makedirs("dados")
        logger.info("Diretório 'dados/' criado.")

    args = parse_args()
    try:
        asyncio.run(main_async(args))
    except Exception as e:
        logger.critical(f"Erro crítico na execução: {e}", exc_info=True)