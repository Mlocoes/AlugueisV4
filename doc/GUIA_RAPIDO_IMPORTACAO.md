# 🚀 Guia Rápido - Importação de Dados

## ⚡ 5 Minutos para Importar Dados

### 1️⃣ Acesse a Página (10 segundos)
```
1. Login como administrador
2. Clique em "Importação" no menu
```

### 2️⃣ Baixe o Modelo (10 segundos)
```
1. Escolha o tipo (Proprietários, Imóveis, etc)
2. Clique em "Baixar Modelo"
3. Abra o arquivo Excel
```

### 3️⃣ Preencha os Dados (3 minutos)
```
✅ NÃO altere os cabeçalhos
✅ Preencha as colunas obrigatórias
✅ Use os exemplos como referência
✅ Salve o arquivo
```

### 4️⃣ Importe (30 segundos)
```
1. Clique em "Selecionar Arquivo"
2. Escolha seu arquivo preenchido
3. Clique em "Importar"
4. Aguarde o resultado
```

### 5️⃣ Verifique (1 minuto)
```
✅ Mensagem verde = Sucesso!
❌ Mensagem vermelha = Corrija os erros e tente novamente
```

---

## 📋 Ordem Recomendada de Importação

Para evitar erros de referência, importe nesta ordem:

```
1º → Proprietários    (não depende de nada)
2º → Imóveis          (não depende de nada)
3º → Participações    (depende de Proprietários + Imóveis)
4º → Aluguéis         (depende de Imóveis)
```

---

## ⚠️ Erros Comuns

### ❌ "Colunas obrigatórias faltando"
**Solução:** Não altere os nomes das colunas. Baixe o modelo novamente.

### ❌ "Imóvel não encontrado"
**Solução:** Importe os imóveis antes de importar aluguéis ou participações.

### ❌ "Soma das participações ≠ 100%"
**Solução:** Verifique que os percentuais por imóvel somam 100%.

### ❌ "Email inválido"
**Solução:** Certifique-se de que o email contém @

---

## 💡 Dicas Importantes

✅ **Teste com poucos dados primeiro** (2-3 linhas)  
✅ **Verifique os dados antes de importar** (tipos, formatos)  
✅ **Use os exemplos do modelo como guia**  
✅ **Para participações, sempre some 100% por imóvel**  
✅ **Datas no formato YYYY-MM-DD** (ex: 2024-01-15)

---

## 📞 Precisa de Ajuda?

Consulte a **documentação completa** em: `IMPORTACAO_EXCEL.md`

Lá você encontrará:
- Descrição detalhada de cada coluna
- Exemplos completos
- Troubleshooting avançado
- Informações técnicas

---

**Bom trabalho! 🎉**
