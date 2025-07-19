#!/usr/bin/env python3
"""
Script para adicionar o campo 'descricao_processada' aos documentos do dados.json
baseado nos IDs encontrados em descricao_processada_2.json
"""

import json
from pathlib import Path


def main():
    # Caminhos dos arquivos
    descricao_path = Path("/Users/institutorecriare/VSCodeProjects/dados/novos/novos_resultados/descricao_processada_2.json")
    dados_path = Path("/Users/institutorecriare/VSCodeProjects/dados/novos/dados/dados.json")
    output_path = Path("/Users/institutorecriare/VSCodeProjects/dados/dados_processados.json")
    
    print("Lendo arquivo de descrições processadas...")
    with open(descricao_path, 'r', encoding='utf-8') as f:
        descricao_data = json.load(f)
    
    # Criar um dicionário para mapear ID -> descricao_processada
    descricao_map = {}
    for item in descricao_data['resultados']:
        descricao_map[item['id']] = item['descricao_processada']
    
    print(f"Encontradas {len(descricao_map)} descrições processadas")
    
    print("Lendo arquivo de dados originais...")
    with open(dados_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    print(f"Encontrados {len(dados)} documentos originais")
    
    # Processar cada documento
    dados_processados = []
    count_updated = 0
    
    for doc in dados:
        # Criar uma cópia do documento
        doc_processado = doc.copy()
        
        # Verificar se temos uma descrição processada para este ID
        if doc['id'] in descricao_map:
            # Adicionar o campo descricao_processada no mesmo nível do ID
            doc_processado['descricao_processada'] = descricao_map[doc['id']]
            count_updated += 1
        
        dados_processados.append(doc_processado)
    
    print(f"Adicionadas descrições processadas a {count_updated} documentos")
    
    # Salvar o resultado
    print(f"Salvando resultado em {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dados_processados, f, ensure_ascii=False, indent=2)
    
    print("Processamento concluído!")
    print(f"Total de documentos: {len(dados_processados)}")
    print(f"Documentos com descrição processada: {count_updated}")
    print(f"Documentos sem descrição processada: {len(dados_processados) - count_updated}")


if __name__ == "__main__":
    main()