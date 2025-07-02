import json
import os
import time
import anthropic # Importa a biblioteca da Anthropic

# --- Configuração --- #
# Obtém o diretório onde o script está localizado
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define os caminhos dos arquivos de forma absoluta
INPUT_FILE = os.path.join(script_dir, 'dados_com_id.json')
INSTRUCTIONS_FILE = os.path.join(script_dir, 'instrucoes_para_revisor_meia_porcao.md')
OUTPUT_DIR = os.path.join(script_dir, 'resultados')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'resultados_meia_porcao_real.json') # Novo nome para não sobrescrever a simulação

# --- Validação da Chave de API --- #
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    print("Erro Crítico: A variável de ambiente ANTHROPIC_API_KEY não está definida.")
    print("Por favor, defina a chave da API antes de executar o script.")
    # exit() # Descomente para fazer o script parar se a chave não for encontrada

# Inicializa o cliente da Anthropic
# Certifique-se de que a chave foi definida antes de descomentar a linha abaixo
client = anthropic.Anthropic(api_key=API_KEY)

# --- Funções --- #

def load_json_data(file_path):
    """Carrega dados de um arquivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Erro: Falha ao decodificar JSON de {file_path}")
        return None

def load_instructions(file_path):
    """Carrega o conteúdo de um arquivo de texto."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo de instruções não encontrado em {file_path}")
        return None

def call_claude_api(system_prompt, user_prompt_data):
    """Chama a API da Claude para classificação."""
    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307", # Modelo rápido e de baixo custo, ideal para esta tarefa
            max_tokens=50, # Suficiente para a resposta JSON {"aceita_meia_porcao": bool}
            temperature=0.0, # Queremos uma resposta determinística
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(user_prompt_data, ensure_ascii=False, indent=2)
                }
            ]
        )
        # A resposta da API está em message.content[0].text
        return message.content[0].text
    except Exception as e:
        print(f"  -> Erro na chamada da API: {e}")
        return None

def main():
    """Função principal para orquestrar o processo."""
    if not API_KEY:
        print("Script não pode continuar sem a chave da API.")
        return
        
    print("Iniciando o script de análise de meia porção (com chamada real à API)...")

    # 1. Carregar dados e instruções
    alimentos = load_json_data(INPUT_FILE)
    instructions = load_instructions(INSTRUCTIONS_FILE)

    if not alimentos or not instructions:
        print("Script encerrado devido a erro na leitura dos arquivos.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Diretório de resultados garantido em: {OUTPUT_DIR}")

    # 2. Processar cada alimento
    resultados = []
    total_items = len(alimentos)
    print(f"Processando {total_items} alimentos...")

    for i, alimento in enumerate(alimentos):
        item_id = alimento.get('id')
        nome_cardapio = alimento.get('nome_cardapio', 'Não especificado')
        unidade_caseira = alimento.get('unidadeCaseira', 'Não especificado')

        if item_id is None:
            print(f"Aviso: Item {i} não possui ID. Pulando.")
            continue

        print(f"  [{i+1}/{total_items}] ID: {item_id} ({nome_cardapio}) - Chamando API...")
        
        user_prompt = {
            "nome_cardapio": nome_cardapio,
            "unidade_caseira": unidade_caseira
        }

        # 3. Chamar a API real
        response_str = call_claude_api(instructions, user_prompt)
        
        if response_str:
            try:
                # Tenta limpar a string e decodificar o JSON
                clean_response_str = response_str.strip().replace('''json
', '').replace('''', '')
                response_data = json.loads(clean_response_str)
                aceita_meia_porcao = response_data.get('aceita_meia_porcao')

                if isinstance(aceita_meia_porcao, bool):
                    resultados.append({
                        "id": item_id,
                        "aceita_meia_porcao": aceita_meia_porcao
                    })
                    print(f"  -> Resposta recebida: {aceita_meia_porcao}")
                else:
                    print(f"  -> Aviso: Resposta JSON não continha o booleano esperado para o ID {item_id}.")
            except json.JSONDecodeError:
                print(f"  -> Aviso: Falha ao decodificar a resposta JSON da API para o ID {item_id}. Resposta: '{response_str}'")
        else:
            print(f"  -> Aviso: Sem resposta da API para o ID {item_id}. Pulando.")
            
        time.sleep(0.5) # Pausa para não sobrecarregar a API

    # 4. Salvar os resultados
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        print(f"\nResultados salvos com sucesso em: {OUTPUT_FILE}")
        print(f"Total de {len(resultados)} resultados foram salvos.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo de resultados: {e}")

if __name__ == "__main__":
    main()