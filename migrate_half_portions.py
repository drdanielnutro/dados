#!/usr/bin/env python3
"""
Script de Migração para Sistema de Meio Porções
Diet Hero - Banco de Dados MongoDB

Este script converte o sistema atual de porções inteiras (incremento de 1.0)
para um sistema de meio porções (incremento de 0.5), dividindo por 2 todos os
valores nutricionais por porção.

Autor: Equipe Diet Hero
Data: Janeiro 2025
Versão: 1.0.0
"""

import json
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse
import logging

# Configuração de logging
def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Configura o sistema de logging"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f'migration_{timestamp}.log'
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"📝 Log salvo em: {log_filename}")
    return logger

logger = setup_logging()

class DietHeroMigration:
    """
    Classe principal para migração do banco de dados Diet Hero
    """
    
    # Campos que devem ser divididos por 2
    CAMPOS_NUTRICIONAIS = [
        # Calorias e macronutrientes processados
        "kcalItem",
        "caloriasCarboidratosItem", 
        "caloriasProteinasItem",
        "caloriasLipidiosItem",
        
        # Quantidade base e energia
        "Quant",
        "Energia_kcal",
        "pesoPorcao",
        
        # Macronutrientes base (gramas)
        "Ptn",
        "G_tot", 
        "G_sat",
        "G_trans",
        "Carb",
        "Fibra",
        
        # Micronutrientes (mg/mcg)
        "Ca_mg",
        "Fe_mg",
        "Na_mg", 
        "Vit_A_mcg",
        "Vit_C_mg"
    ]
    
    # Campos que NÃO devem ser alterados
    CAMPOS_INALTERADOS = [
        "_id", "alimento", "nome_cardapio", "nome_cotidiano",
        "porcaoMax", "porcaoItem", "macroTipo", "saudavel",
        "grupoAlimentarString", "descricao_processada", 
        "unidadeCaseira", "unidadesCaseira", "filtro", "filtro_2",
        "unidadeMetrica", "image", "url_2", "prompt", "prompt_corrigido",
        "ordemDoGrupo", "ordenacao", "categoria", "description", 
        "gpt", "passoA", "refeicaoPertencenteString", "uploadColorido"
    ]
    
    def __init__(self, arquivo_entrada: str, arquivo_saida: Optional[str] = None):
        """
        Inicializa a migração
        
        Args:
            arquivo_entrada: Caminho para o arquivo JSON de entrada
            arquivo_saida: Caminho para o arquivo JSON de saída (opcional)
        """
        self.arquivo_entrada = os.path.abspath(arquivo_entrada)
        self.arquivo_saida = arquivo_saida or self._gerar_nome_saida()
        self.backup_arquivo = self._gerar_nome_backup()
        self.estatisticas = {
            'total_documentos': 0,
            'documentos_processados': 0,
            'campos_modificados': 0,
            'erros': 0,
            'documentos_com_erro': []
        }
        
    def _gerar_nome_saida(self) -> str:
        """Gera nome do arquivo de saída baseado no arquivo de entrada"""
        base, ext = os.path.splitext(self.arquivo_entrada)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base}_migrated_{timestamp}{ext}"
    
    def _gerar_nome_backup(self) -> str:
        """Gera nome do arquivo de backup"""
        base, ext = os.path.splitext(self.arquivo_entrada)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
        return f"{base}_backup_{timestamp}{ext}"
    
    def _validar_arquivo_entrada(self) -> bool:
        """
        Valida se o arquivo de entrada existe e é válido
        
        Returns:
            bool: True se válido, False caso contrário
        """
        if not os.path.exists(self.arquivo_entrada):
            logger.error(f"❌ Arquivo de entrada não encontrado: {self.arquivo_entrada}")
            return False
            
        try:
            with open(self.arquivo_entrada, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
            if not isinstance(dados, list):
                logger.error("❌ Arquivo deve conter um array JSON de documentos")
                return False
                
            if len(dados) == 0:
                logger.error("❌ Arquivo contém um array vazio")
                return False
                
            logger.info(f"✅ Arquivo de entrada válido: {self.arquivo_entrada}")
            logger.info(f"📊 Contém {len(dados)} documentos")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Arquivo JSON inválido: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao validar arquivo: {e}")
            return False
    
    def _criar_backup(self) -> bool:
        """
        Cria backup do arquivo original
        
        Returns:
            bool: True se backup criado com sucesso
        """
        try:
            shutil.copy2(self.arquivo_entrada, self.backup_arquivo)
            size_mb = os.path.getsize(self.backup_arquivo) / (1024 * 1024)
            logger.info(f"✅ Backup criado: {self.backup_arquivo} ({size_mb:.1f} MB)")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return False
    
    def _processar_documento(self, documento: Dict[str, Any], indice: int) -> Dict[str, Any]:
        """
        Processa um documento individual, dividindo por 2 os campos nutricionais
        
        Args:
            documento: Dicionário representando um documento/alimento
            indice: Índice do documento na lista (para logging)
            
        Returns:
            Dict: Documento processado
        """
        documento_processado = documento.copy()
        campos_modificados_doc = 0
        
        try:
            # Processar cada campo nutricional
            for campo in self.CAMPOS_NUTRICIONAIS:
                if campo in documento:
                    valor_original = documento[campo]
                    
                    # Verificar se é um número
                    if isinstance(valor_original, (int, float)):
                        valor_novo = valor_original / 2.0
                        documento_processado[campo] = valor_novo
                        campos_modificados_doc += 1
                        
                        logger.debug(
                            f"  📝 {campo}: {valor_original} → {valor_novo} "
                            f"(doc {indice}: {documento.get('alimento', 'Sem nome')})"
                        )
                    elif valor_original is not None:  # Não é None mas também não é número
                        logger.warning(
                            f"⚠️  Campo {campo} não é numérico no documento {indice}: "
                            f"{valor_original} (tipo: {type(valor_original)})"
                        )
            
            # Adicionar metadados de migração
            documento_processado['_migration'] = {
                'migrated_at': datetime.now().isoformat(),
                'version': '0.5_portions',
                'campos_modificados': campos_modificados_doc,
                'script_version': '1.0.0',
                'original_id': documento.get('_id', documento.get('alimento', f'doc_{indice}'))
            }
            
            self.estatisticas['campos_modificados'] += campos_modificados_doc
            self.estatisticas['documentos_processados'] += 1
            
            # Log de progresso a cada 100 documentos
            if (indice + 1) % 100 == 0:
                logger.info(f"🔄 Processados {indice + 1}/{self.estatisticas['total_documentos']} documentos...")
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar documento {indice}: {e}")
            logger.error(f"   Documento: {documento.get('alimento', 'Sem nome')}")
            self.estatisticas['erros'] += 1
            self.estatisticas['documentos_com_erro'].append({
                'indice': indice,
                'alimento': documento.get('alimento', 'Sem nome'),
                'erro': str(e)
            })
            # Retorna documento original em caso de erro
            return documento
            
        return documento_processado
    
    def _validar_documento_processado(self, original: Dict[str, Any], 
                                    processado: Dict[str, Any]) -> bool:
        """
        Valida se o documento foi processado corretamente
        
        Args:
            original: Documento original
            processado: Documento processado
            
        Returns:
            bool: True se válido
        """
        try:
            # Verificar se campos inalterados não foram modificados
            for campo in self.CAMPOS_INALTERADOS:
                if campo in original:
                    if original[campo] != processado[campo]:
                        logger.error(f"❌ Campo inalterado foi modificado: {campo}")
                        logger.error(f"   Original: {original[campo]}")
                        logger.error(f"   Processado: {processado[campo]}")
                        return False
            
            # Verificar se campos nutricionais foram divididos corretamente
            for campo in self.CAMPOS_NUTRICIONAIS:
                if campo in original and isinstance(original[campo], (int, float)):
                    esperado = original[campo] / 2.0
                    if abs(processado[campo] - esperado) > 0.0001:  # Tolerância para float
                        logger.error(f"❌ Campo {campo} não foi dividido corretamente")
                        logger.error(f"   Original: {original[campo]}")
                        logger.error(f"   Esperado: {esperado}")
                        logger.error(f"   Processado: {processado[campo]}")
                        return False
            
            # Verificar se metadados de migração foram adicionados
            if '_migration' not in processado:
                logger.error("❌ Metadados de migração não foram adicionados")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na validação: {e}")
            return False
    
    def _validar_integridade_arquivo(self, arquivo: str) -> bool:
        """
        Valida se um arquivo JSON é válido e contém dados esperados
        
        Args:
            arquivo: Caminho para o arquivo
            
        Returns:
            bool: True se válido
        """
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
            if not isinstance(dados, list):
                logger.error(f"❌ Arquivo {arquivo} não contém um array")
                return False
                
            if len(dados) == 0:
                logger.error(f"❌ Arquivo {arquivo} contém array vazio")
                return False
                
            # Verificar se tem pelo menos os campos básicos esperados
            primeiro_doc = dados[0]
            campos_basicos = ['alimento', 'kcalItem', 'Quant']
            for campo in campos_basicos:
                if campo not in primeiro_doc:
                    logger.warning(f"⚠️  Campo básico '{campo}' não encontrado no primeiro documento")
                    
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar integridade do arquivo {arquivo}: {e}")
            return False
    
    def executar_migracao(self, validar_resultado: bool = True) -> bool:
        """
        Executa a migração completa
        
        Args:
            validar_resultado: Se deve validar cada documento processado
            
        Returns:
            bool: True se migração bem-sucedida
        """
        logger.info("🚀 Iniciando migração para sistema de meio porções...")
        logger.info(f"📁 Arquivo de entrada: {self.arquivo_entrada}")
        logger.info(f"📁 Arquivo de saída: {self.arquivo_saida}")
        
        # Validações iniciais
        if not self._validar_arquivo_entrada():
            return False
            
        if not self._criar_backup():
            logger.error("❌ Falha na criação do backup. Abortando migração por segurança.")
            return False
        
        try:
            # Carregar dados
            logger.info("📖 Carregando dados do arquivo...")
            with open(self.arquivo_entrada, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            self.estatisticas['total_documentos'] = len(dados)
            logger.info(f"📊 Total de documentos para processar: {len(dados)}")
            
            # Processar documentos
            logger.info("🔄 Processando documentos...")
            dados_processados = []
            
            for i, documento in enumerate(dados):
                documento_processado = self._processar_documento(documento, i)
                
                # Validar se solicitado
                if validar_resultado:
                    if not self._validar_documento_processado(documento, documento_processado):
                        logger.error(f"❌ Falha na validação do documento {i}")
                        logger.error(f"   Alimento: {documento.get('alimento', 'Sem nome')}")
                        return False
                
                dados_processados.append(documento_processado)
            
            # Salvar resultado
            logger.info(f"💾 Salvando resultado em {self.arquivo_saida}...")
            with open(self.arquivo_saida, 'w', encoding='utf-8') as f:
                json.dump(dados_processados, f, ensure_ascii=False, indent=2)
            
            # Verificar integridade do arquivo salvo
            if not self._validar_integridade_arquivo(self.arquivo_saida):
                logger.error("❌ Arquivo salvo falhou na validação de integridade")
                return False
            
            # Relatório final
            self._gerar_relatorio_final()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante a migração: {e}")
            logger.error(f"   Stack trace completo:", exc_info=True)
            return False
    
    def _gerar_relatorio_final(self):
        """Gera relatório final da migração"""
        
        # Calcular estatísticas
        taxa_sucesso = (self.estatisticas['documentos_processados'] / 
                       self.estatisticas['total_documentos'] * 100) if self.estatisticas['total_documentos'] > 0 else 0
        
        # Tamanhos dos arquivos
        try:
            size_original = os.path.getsize(self.arquivo_entrada) / (1024 * 1024)
            size_migrado = os.path.getsize(self.arquivo_saida) / (1024 * 1024)
            size_backup = os.path.getsize(self.backup_arquivo) / (1024 * 1024)
        except:
            size_original = size_migrado = size_backup = 0
        
        logger.info("\n" + "="*60)
        logger.info("📋 RELATÓRIO FINAL DA MIGRAÇÃO")
        logger.info("="*60)
        logger.info(f"📊 Total de documentos: {self.estatisticas['total_documentos']}")
        logger.info(f"✅ Documentos processados: {self.estatisticas['documentos_processados']}")
        logger.info(f"🔧 Campos modificados: {self.estatisticas['campos_modificados']}")
        logger.info(f"❌ Erros encontrados: {self.estatisticas['erros']}")
        logger.info(f"📈 Taxa de sucesso: {taxa_sucesso:.2f}%")
        logger.info("")
        logger.info("📁 ARQUIVOS:")
        logger.info(f"   📥 Original:  {self.arquivo_entrada} ({size_original:.1f} MB)")
        logger.info(f"   📤 Migrado:   {self.arquivo_saida} ({size_migrado:.1f} MB)")
        logger.info(f"   🔄 Backup:    {self.backup_arquivo} ({size_backup:.1f} MB)")
        
        if self.estatisticas['erros'] > 0:
            logger.warning(f"\n⚠️  DOCUMENTOS COM ERRO ({self.estatisticas['erros']}):")
            for i, erro in enumerate(self.estatisticas['documentos_com_erro'][:10]):  # Mostrar max 10
                logger.warning(f"   {i+1}. Índice {erro['indice']}: {erro['alimento']} - {erro['erro']}")
            
            if len(self.estatisticas['documentos_com_erro']) > 10:
                restantes = len(self.estatisticas['documentos_com_erro']) - 10
                logger.warning(f"   ... e mais {restantes} erros.")
        
        logger.info("="*60)
        
        if taxa_sucesso == 100.0:
            logger.info("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        elif taxa_sucesso >= 95.0:
            logger.warning("⚠️  MIGRAÇÃO CONCLUÍDA COM AVISOS MENORES - Verifique os erros acima")
        else:
            logger.error("❌ MIGRAÇÃO CONCLUÍDA COM PROBLEMAS SIGNIFICATIVOS - Revise antes de usar")
    
    def validar_integridade(self) -> bool:
        """
        Valida a integridade dos dados migrados comparando com o original
        
        Returns:
            bool: True se integridade mantida
        """
        logger.info("🔍 Validando integridade dos dados migrados...")
        
        try:
            # Carregar dados originais e migrados
            with open(self.arquivo_entrada, 'r', encoding='utf-8') as f:
                dados_originais = json.load(f)
                
            with open(self.arquivo_saida, 'r', encoding='utf-8') as f:
                dados_migrados = json.load(f)
            
            if len(dados_originais) != len(dados_migrados):
                logger.error("❌ Quantidade de documentos difere entre original e migrado")
                logger.error(f"   Original: {len(dados_originais)} documentos")
                logger.error(f"   Migrado: {len(dados_migrados)} documentos")
                return False
            
            # Validar cada documento
            erros_validacao = 0
            for i, (original, migrado) in enumerate(zip(dados_originais, dados_migrados)):
                if not self._validar_documento_processado(original, migrado):
                    erros_validacao += 1
                    if erros_validacao <= 5:  # Mostrar apenas os primeiros 5 erros
                        logger.error(f"❌ Erro de integridade no documento {i}: {original.get('alimento', 'Sem nome')}")
            
            if erros_validacao == 0:
                logger.info("✅ Integridade dos dados validada com sucesso!")
                return True
            else:
                logger.error(f"❌ {erros_validacao} erros de integridade encontrados")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro durante validação de integridade: {e}")
            return False
    
    def gerar_relatorio_comparativo(self) -> Dict[str, Any]:
        """
        Gera um relatório comparativo entre dados originais e migrados
        
        Returns:
            Dict: Relatório com estatísticas comparativas
        """
        logger.info("📊 Gerando relatório comparativo...")
        
        try:
            with open(self.arquivo_entrada, 'r', encoding='utf-8') as f:
                dados_originais = json.load(f)
                
            with open(self.arquivo_saida, 'r', encoding='utf-8') as f:
                dados_migrados = json.load(f)
            
            relatorio = {
                'total_documentos': len(dados_originais),
                'campos_analisados': {},
                'amostras_comparacao': []
            }
            
            # Analisar alguns campos específicos
            for campo in ['kcalItem', 'Quant', 'pesoPorcao']:
                if dados_originais and campo in dados_originais[0]:
                    valores_originais = [doc.get(campo, 0) for doc in dados_originais[:5]]
                    valores_migrados = [doc.get(campo, 0) for doc in dados_migrados[:5]]
                    
                    relatorio['campos_analisados'][campo] = {
                        'originais': valores_originais,
                        'migrados': valores_migrados,
                        'razao_media': sum(v_orig / v_mig if v_mig != 0 else 0 for v_orig, v_mig in zip(valores_originais, valores_migrados)) / len(valores_originais)
                    }
            
            # Amostras de comparação (primeiros 3 documentos)
            for i in range(min(3, len(dados_originais))):
                original = dados_originais[i]
                migrado = dados_migrados[i]
                
                amostra = {
                    'indice': i,
                    'alimento': original.get('alimento', 'Sem nome'),
                    'comparacao': {}
                }
                
                for campo in self.CAMPOS_NUTRICIONAIS[:5]:  # Primeiros 5 campos
                    if campo in original:
                        amostra['comparacao'][campo] = {
                            'original': original[campo],
                            'migrado': migrado.get(campo, 'N/A'),
                            'diferenca_relativa': f"{((migrado.get(campo, 0) / original[campo]) - 0.5) * 100:.2f}%" if original[campo] != 0 else 'N/A'
                        }
                
                relatorio['amostras_comparacao'].append(amostra)
            
            # Salvar relatório
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo_relatorio = f"relatorio_comparativo_{timestamp}.json"
            with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📊 Relatório comparativo salvo em: {arquivo_relatorio}")
            return relatorio
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório comparativo: {e}")
            return {}

def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description="Migração Diet Hero: Sistema de Meio Porções",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 Exemplos de uso:

Uso básico:
  python migrate_half_portions.py ../docs/dados.json

Com validação completa:
  python migrate_half_portions.py ../docs/dados.json --validate

Arquivo de saída específico:
  python migrate_half_portions.py dados.json --output dados_migrados.json

Com relatório comparativo:
  python migrate_half_portions.py dados.json --validate --report

Apenas validar arquivos existentes:
  python migrate_half_portions.py original.json --validate-only migrado.json

📋 Campos que serão modificados (divididos por 2):
  - Valores nutricionais: kcalItem, caloriasCarboidratosItem, etc.
  - Quantidades: Quant, pesoPorcao, etc.
  - Macronutrientes: Ptn, G_tot, Carb, Fibra, etc.
  - Micronutrientes: Ca_mg, Fe_mg, Vit_C_mg, etc.

🔒 Campos preservados:
  - IDs e nomes: _id, alimento, nome_cardapio, etc.
  - Configurações: porcaoMax, porcaoItem, macroTipo, etc.
  - Metadados: unidadeMetrica, image, prompt, etc.
        """
    )
    
    parser.add_argument(
        'arquivo_entrada',
        help='Arquivo JSON de entrada com os dados dos alimentos'
    )
    
    parser.add_argument(
        '--output', '-o',
        dest='arquivo_saida',
        help='Arquivo JSON de saída (opcional, será gerado automaticamente se não especificado)'
    )
    
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help='Validar integridade após migração'
    )
    
    parser.add_argument(
        '--validate-only',
        dest='arquivo_migrado',
        help='Apenas validar um arquivo já migrado (comparar com original)'
    )
    
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='Gerar relatório comparativo detalhado'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true', 
        help='Não criar backup do arquivo original (não recomendado)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Nível de logging (padrão: INFO)'
    )
    
    args = parser.parse_args()
    
    # Reconfigurar logging com nível especificado
    global logger
    logger = setup_logging(args.log_level)
    
    # Modo de validação apenas
    if args.arquivo_migrado:
        logger.info("🔍 Modo validação apenas...")
        migration = DietHeroMigration(args.arquivo_entrada, args.arquivo_migrado)
        if migration.validar_integridade():
            logger.info("✅ Validação concluída com sucesso!")
            sys.exit(0)
        else:
            logger.error("❌ Validação falhou!")
            sys.exit(1)
    
    # Criar instância da migração
    migration = DietHeroMigration(args.arquivo_entrada, args.arquivo_saida)
    
    # Executar migração
    sucesso = migration.executar_migracao(validar_resultado=True)
    
    if sucesso:
        if args.validate:
            logger.info("\n🔍 Executando validação adicional...")
            if not migration.validar_integridade():
                logger.error("❌ Falha na validação adicional!")
                sys.exit(1)
        
        if args.report:
            logger.info("\n📊 Gerando relatório comparativo...")
            migration.gerar_relatorio_comparativo()
        
        logger.info("\n🎉 Processo concluído com sucesso!")
        logger.info(f"📁 Arquivo migrado: {migration.arquivo_saida}")
        logger.info(f"🔄 Backup original: {migration.backup_arquivo}")
        
        # Instruções finais
        logger.info("\n📋 PRÓXIMOS PASSOS:")
        logger.info("1. 📋 Revisar o relatório de migração acima")
        logger.info("2. 🧪 Testar o arquivo migrado em ambiente de desenvolvimento")
        logger.info("3. 🔧 Atualizar o código da função calculoPorcoes.js")
        logger.info("4. 🚀 Fazer deploy em produção")
        
        sys.exit(0)
    else:
        logger.error("❌ Processo falhou!")
        logger.error(f"🔄 Backup disponível em: {migration.backup_arquivo}")
        sys.exit(1)

if __name__ == "__main__":
    main()