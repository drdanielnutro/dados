# Guia de Configuração para Agentes IA

Este documento explica como configurar o ambiente para executar o sistema de classificação de porções usando a API da Anthropic.

## Pré-requisitos

### 1. Python
- Python 3.7 ou superior instalado
- pip (gerenciador de pacotes do Python)

### 2. Chave de API da Anthropic
Você precisa de uma chave de API válida da Anthropic para usar o Claude. 

Para obter uma chave:
1. Acesse https://console.anthropic.com/
2. Crie uma conta ou faça login
3. Navegue até a seção de API Keys
4. Crie uma nova chave de API
5. Copie a chave (ela começa com `sk-ant-api...`)

## Instalação das Dependências

### 1. Instalar os pacotes Python necessários

```bash
pip install -r requirements.txt
```

Isso instalará:
- **anthropic**: SDK oficial da Anthropic para Python
- **pydantic**: Biblioteca para validação de dados
- **python-dotenv**: Para carregar variáveis de ambiente do arquivo .env
- **asyncio**: Para processamento assíncrono (geralmente já vem com Python)

### 2. Configurar a chave de API

Crie um arquivo `.env` na raiz do projeto:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-api-sua-chave-aqui" > .env
```

**IMPORTANTE**: 
- Substitua `sk-ant-api-sua-chave-aqui` pela sua chave real
- NUNCA commite o arquivo .env no git (já está no .gitignore)
- Mantenha sua chave de API segura e privada

## Verificando a Instalação

Para verificar se tudo está configurado corretamente:

```python
# teste_api.py
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

try:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=50,
        messages=[{"role": "user", "content": "Olá, teste de API!"}]
    )
    print("✅ API configurada com sucesso!")
    print(f"Resposta: {response.content[0].text}")
except Exception as e:
    print(f"❌ Erro na configuração: {e}")
```

## Executando o Sistema

Após a configuração:

```bash
python meia_porcao.py
```

## Custos e Limites

### Modelo Claude Sonnet 4
- **Input**: $3 por milhão de tokens
- **Output**: $15 por milhão de tokens
- Para esta aplicação, cada classificação usa aproximadamente 200-300 tokens no total

### Estimativa de custos:
- 1.000 classificações ≈ $0.01 - $0.02
- 10.000 classificações ≈ $0.10 - $0.20

## Troubleshooting

### Erro: "ANTHROPIC_API_KEY não foi encontrada"
- Verifique se o arquivo .env existe e contém a chave
- Certifique-se de que está executando o script do diretório correto

### Erro: "Invalid API Key"
- Verifique se copiou a chave completa
- Confirme se a chave está ativa no console da Anthropic

### Erro: "Rate limit exceeded"
- Reduza o parâmetro `--max_concurrent` (padrão: 5)
- Adicione delays entre requisições se necessário

## Parâmetros de Otimização

Para ajustar o comportamento da API:

```bash
# Processar apenas 10 itens por vez
python meia_porcao.py --max_items 10

# Reduzir concorrência para 2 requisições simultâneas
python meia_porcao.py --max_concurrent 2

# Usar temperatura diferente (0.0 = mais determinístico)
python meia_porcao.py --temperature 0.0
```

## Segurança

1. **Nunca compartilhe sua chave de API**
2. Use variáveis de ambiente em vez de hardcode
3. Adicione limites de rate para evitar custos inesperados
4. Monitore o uso no console da Anthropic
5. Considere criar chaves separadas para desenvolvimento e produção

## Suporte

Para problemas com:
- **Este código**: Abra uma issue no GitHub
- **API da Anthropic**: https://support.anthropic.com/
- **Limites e custos**: Console da Anthropic