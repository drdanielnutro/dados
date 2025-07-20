#!/usr/bin/env python3
"""
Script para remover o campo 'comentarios' de todos os documentos em um arquivo JSON.
Cria um backup antes de fazer qualquer modificação.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import shutil


def criar_backup(arquivo_original):
    """Cria backup do arquivo original com timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_backup = f"{arquivo_original.stem}_backup_{timestamp}{arquivo_original.suffix}"
    arquivo_backup_path = arquivo_original.parent / arquivo_backup
    
    print(f"Criando backup: {arquivo_backup_path}")
    shutil.copy2(arquivo_original, arquivo_backup_path)
    return arquivo_backup_path


def remover_campo_comentarios(arquivo_entrada, arquivo_saida=None):
    """
    Remove o campo 'comentarios' de todos os documentos no arquivo JSON.
    
    Args:
        arquivo_entrada: Path do arquivo JSON de entrada
        arquivo_saida: Path do arquivo de saída (opcional)
    """
    arquivo_entrada = Path(arquivo_entrada)
    
    if not arquivo_entrada.exists():
        print(f"Erro: Arquivo {arquivo_entrada} não encontrado.")
        return
    
    # Criar backup
    backup_path = criar_backup(arquivo_entrada)
    print(f"Backup criado em: {backup_path}")
    
    # Ler dados
    print(f"\nLendo arquivo: {arquivo_entrada}")
    with open(arquivo_entrada, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    # Estatísticas
    total_docs = len(dados)
    docs_modificados = 0
    
    # Processar documentos
    print(f"Processando {total_docs} documentos...")
    for doc in dados:
        if 'comentarios' in doc:
            del doc['comentarios']
            docs_modificados += 1
    
    # Definir arquivo de saída
    if arquivo_saida is None:
        arquivo_saida = arquivo_entrada
    else:
        arquivo_saida = Path(arquivo_saida)
    
    # Salvar resultado
    print(f"\nSalvando resultado em: {arquivo_saida}")
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    # Exibir estatísticas
    print(f"\n=== Estatísticas ===")
    print(f"Total de documentos: {total_docs}")
    print(f"Documentos modificados: {docs_modificados}")
    print(f"Campo 'comentarios' removido de {docs_modificados} documentos")
    
    if arquivo_saida == arquivo_entrada:
        print(f"\nArquivo original foi atualizado.")
        print(f"Backup disponível em: {backup_path}")
    else:
        print(f"\nNovo arquivo criado: {arquivo_saida}")
        print(f"Arquivo original preservado em: {arquivo_entrada}")


def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python remover_comentarios.py <arquivo_json> [arquivo_saida]")
        print("\nExemplos:")
        print("  python remover_comentarios.py dados_processados3.json")
        print("  python remover_comentarios.py dados_processados3.json dados_sem_comentarios.json")
        sys.exit(1)
    
    arquivo_entrada = sys.argv[1]
    arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else None
    
    remover_campo_comentarios(arquivo_entrada, arquivo_saida)


if __name__ == "__main__":
    main()