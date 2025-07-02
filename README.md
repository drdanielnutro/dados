# Sistema de Classificação de Porções de Alimentos

Sistema que utiliza Claude AI para classificar alimentos quanto à aceitabilidade de "meia porção" no contexto brasileiro.

## Descrição

Este projeto analisa uma lista de alimentos e determina automaticamente se cada item aceita "meia porção" baseando-se em critérios culturais e práticos do contexto brasileiro. A decisão é tomada considerando a combinação entre o nome do alimento e sua unidade de medida caseira.

## Funcionalidades

- Análise automática de alimentos usando Claude Sonnet 4
- Classificação binária (aceita/não aceita meia porção)
- Controle de processamento para evitar reprocessamento
- Processamento assíncrono com controle de concorrência
- Logs detalhados de execução

## Requisitos

- Python 3.7+
- Chave de API da Anthropic (Claude)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/drdanielnutro/dados.git
cd dados
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure a chave de API:
```bash
# Crie um arquivo .env na raiz do projeto
echo "ANTHROPIC_API_KEY=sua_chave_aqui" > .env
```

## Uso

Execute o script com os parâmetros padrão:
```bash
python meia_porcao.py
```

### Parâmetros opcionais:

- `--input`: Arquivo JSON de entrada (padrão: `dados_com_id.json`)
- `--max_items`: Número máximo de itens a processar (padrão: 100)
- `--max_concurrent`: Requisições concorrentes (padrão: 5)
- `--temperature`: Temperature da API (padrão: 0.0)

## Estrutura dos Dados

### Entrada (dados_com_id.json):
```json
[
  {
    "id": 0,
    "nome_cardapio": "Abacate manteiga in natura",
    "unidadeCaseira": "colher de sopa cheia (PICADO)",
    ...
  }
]
```

### Saída:
```json
{
  "total_analisados": 10,
  "total_aceita_meia_porcao_true": 6,
  "total_aceita_meia_porcao_false": 4,
  "resultados": [
    {
      "id": 0,
      "nome_cardapio": "Abacate manteiga in natura",
      "unidadeCaseira": "colher de sopa cheia (PICADO)",
      "aceita_meia_porcao": false
    }
  ]
}
```

## Arquivos Gerados

- `classificacao_porcoes.log`: Log de execução
- `dados/ids_alimentos_analisados.txt`: Controle de IDs processados
- `dados/resultados_meia_porcao/classificacao_porcoes_N.json`: Resultados da classificação

## Licença

Este projeto está licenciado sob a licença MIT.