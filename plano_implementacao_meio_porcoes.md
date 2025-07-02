# 📋 Plano de Implementação: Sistema de Meio Porções

**Data de Criação:** 13/06/2025  
**Objetivo:** Migrar sistema de porções inteiras (incremento 1.0) para meio porções (incremento 0.5)  
**Status:** Em Planejamento

---


## 🔴 **TAREFAS CRÍTICAS (Alta Prioridade)**

Fazer commit e push antes de começar.

### **Task 001: Atualizar UpdatedSelectedItemsAppStateStruct**
- **Descrição:** Mudar `porcaoItem` de `int` para `double` na struct principal
- **Arquivo:** `/lib/backend/schema/structs/updated_selected_items_app_state_struct.dart`
- **Status:** ⏳ Pendente
- **Prioridade:** Alta

### **Task 002: Modificar função calculoPorcoes.js**
- **Descrição:** Alterar incremento de `porcaoItem` de `1` para `0.5`
- **Arquivo:** `/firebase/functions/lib/modules/calculoPorcoes.js` (linha 950)
- **Mudança:** `const novaPorcaoItem = porcaoAtual + 0.5;`
- **Status:** ⏳ Pendente
- **Prioridade:** Alta

### **Task 003: Implementar mensagem "Em atualização"**
- **Descrição:** Proteger páginas que ainda não suportam meio porções
- **Arquivo:** `/lib/pages/teste_nova_home/teste_nova_home_widget.dart`
- **Funcionalidades afetadas:** Sobremesas e Refeição Livre
- **Status:** ⏳ Pendente
- **Prioridade:** Alta

### **Task 004: Executar migração MongoDB**
- **Descrição:** Dividir valores nutricionais por 2 usando script de migração
- **Script:** `/dados/migrate_half_portions.py`
- **Comando:** `python migrate_half_portions.py dados.json --validate --report`
- **Status:** ⏳ Pendente
- **Prioridade:** Alta
- **⚠️ CRÍTICO:** Fazer backup completo antes da execução

### **Task 005: Solução para calculoLS**
- **Descrição:** Migrar dados do Firebase/Firestore para suportar meio porções
- **Problema:** Página calculoLS ainda processa dados não divididos por 2
- **Status:** ⏳ Pendente
- **Prioridade:** Alta

### **Task 006: Atualizar outras structs**
- **Descrição:** Mudar `porcaoItem` de `int` para `double` em structs relacionadas
- **Arquivos:**
  - `/lib/backend/schema/structs/selected_items_struct.dart`
  - `/lib/backend/schema/structs/alimento_struct.dart`
- **Status:** ⏳ Pendente
- **Prioridade:** Média

---

## 🟡 **TAREFAS DE VALIDAÇÃO (Média Prioridade)**

### **Task 007: Testar fluxo completo**
- **Descrição:** Validar assistente coach (entrada → cálculo → exibição)
- **Cenários de teste:**
  - Entrada por texto
  - Entrada por voz
  - Cálculo de alimentos
  - Cálculo de sobremesas
  - Exibição de resultados
- **Status:** ⏳ Pendente
- **Prioridade:** Média

### **Task 008: Verificar inconsistências**
- **Descrição:** Encontrar e corrigir páginas que usam `porcaoItem` como `int`
- **Método:** Busca global por `porcaoItem` no código
- **Status:** ⏳ Pendente
- **Prioridade:** Média

---

## 🟢 **TAREFAS DE FINALIZAÇÃO (Baixa Prioridade)**

### **Task 009: Remover mensagem "Em atualização"**
- **Descrição:** Restaurar funcionalidade completa após testes
- **Condição:** Todos os testes passando
- **Status:** ⏳ Pendente
- **Prioridade:** Baixa

---

## 🚨 **PONTOS CRÍTICOS DE ATENÇÃO**

### **Ordem de Execução Obrigatória**
1. ✅ Tasks 001-003 (Preparação)
2. ✅ Task 004 (Migração MongoDB)
3. ✅ Task 005 (Migração Firebase)
4. ✅ Tasks 006-008 (Validação)
5. ✅ Task 009 (Finalização)

### **Medidas de Segurança**
- 🔒 **Backup completo** antes da migração
- 🧪 **Teste incremental** após cada etapa
- 🔄 **Plano de rollback** preparado
- 📊 **Monitoramento** durante toda a transição

### **Impacto Esperado**
- ✅ Sistema de meio porções (0.5, 1.0, 1.5...)
- ✅ Maior precisão nutricional
- ✅ Melhor experiência do usuário
- ✅ Compatibilidade mantida

---

## 📊 **Status Resumido**

| Categoria   | Total | Pendente | Em Progresso | Concluído |
| ----------- | ----- | -------- | ------------ | --------- |
| Críticas    | 6     | 6        | 0            | 0         |
| Validação   | 2     | 2        | 0            | 0         |
| Finalização | 1     | 1        | 0            | 0         |
| **TOTAL**   | **9** | **9**    | **0**        | **0**     |

---

## 📝 **Logs de Execução**

### 13/06/2025
- ✅ Plano criado
- ✅ Script de migração analisado
- ✅ Estruturas de dados identificadas
- ⏳ Aguardando início da implementação

---

**Próximos Passos:** Iniciar Task 001 - Atualizar UpdatedSelectedItemsAppStateStruct