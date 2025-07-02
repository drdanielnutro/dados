
import json
import os

# Define os caminhos absolutos baseados no local do script
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, 'dados.json')
output_path = os.path.join(script_dir, 'dados_com_id.json')

print(f"Lendo dados de: {input_path}")

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Adiciona um ID único a cada item
    for i, item in enumerate(data):
        item['id'] = i

    print(f"Adicionando IDs a {len(data)} itens.")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Arquivo 'dados_com_id.json' criado com sucesso em: {output_path}")

except FileNotFoundError:
    print(f"Erro: O arquivo de entrada não foi encontrado em {input_path}")
except json.JSONDecodeError:
    print(f"Erro: Falha ao decodificar o JSON do arquivo {input_path}. Verifique se o formato é válido.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
