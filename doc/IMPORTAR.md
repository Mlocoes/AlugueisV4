Prompt para Funcionalidade de Importação de Dados
Objetivo
Implementar uma funcionalidade de importação que leia arquivos Excel (.xlsx) e importe os dados para o banco de dados, processando informações de proprietários, imóveis, participações e aluguéis.
Arquivos a Serem Importados
1. Proprietario.xlsx
Estrutura da planilha:
•	Colunas: Nome, Sobrenome, Documento, Tipo Documento, Endereço, Telefone, Email
•	Características: 
o	Planilha única
o	Alguns campos podem estar vazios
o	Documento pode conter formatação com pontos, vírgulas e hífens (ex: 170,858,698-95)
o	Tipo Documento geralmente é "CPF"
Regras de importação:
•	Validar formato de documento (CPF)
•	Normalizar documento removendo caracteres especiais para armazenamento
•	Permitir campos opcionais vazios
•	Tratar duplicatas (verificar por documento)
2. Imoveis.xlsx
Estrutura da planilha:
•	Colunas: Nome, Endereço, Tipo, Área Total, Área Construída, Valor Catastral, Valor Mercado, IPTU Anual, Condomínio
•	Características: 
o	Planilha única
o	Valores numéricos com separador de milhares (espaços ou pontos)
o	Separador decimal é vírgula
o	Alguns campos numéricos podem estar vazios
o	Tipo pode ser "Comercial" ou "Residencial"
Regras de importação:
•	Converter valores monetários (remover formatação, converter vírgulas para pontos)
•	Converter áreas para formato numérico decimal
•	Validar que Nome e Endereço sejam únicos
•	Permitir campos numéricos opcionais (área, IPTU, condomínio)
3. Participacao.xlsx
Estrutura da planilha:
•	Colunas: Nome, Endereço, VALOR, [Colunas dinâmicas com nomes dos proprietários]
•	Características: 
o	Primeira coluna: Nome do imóvel
o	Segunda coluna: Endereço do imóvel
o	Terceira coluna: VALOR (sempre 100,000000 %)
o	Demais colunas: Percentuais de participação de cada proprietário
o	Percentuais em formato "XX,XXXXXX %"
o	Soma das participações deve ser 100%
Regras de importação:
•	Relacionar imóvel através de Nome ou Endereço
•	Relacionar proprietários através dos nomes das colunas (Nome + Sobrenome)
•	Converter percentuais para formato decimal (dividir por 100)
•	Criar registros de participação apenas quando percentual > 0
•	Validar que soma de participações = 100% (com tolerância para arredondamento)
4. Aluguel.xlsx
Estrutura especial:
•	MÚLTIPLAS PLANILHAS - uma por mês de referência
•	Primeira linha: Data no formato DD/MM/YYYY (ex: 24/09/2025) que identifica o mês
•	Colunas: 
o	Primeira coluna: Nome/Endereço do imóvel
o	Segunda coluna: Valor Total
o	Colunas seguintes: Valores distribuídos por proprietário (nomes dos proprietários)
o	Última coluna: Taxa de Administração
Características:
•	Valores podem ser negativos (representados com hífen: "- 1.863,76")
•	Formato monetário com separadores de milhares e vírgula decimal
•	Valores vazios representados por "-" ou em branco
•	Cada planilha representa um mês diferente
Regras de importação:
•	Iterar sobre todas as planilhas do arquivo
•	Extrair data de referência da primeira célula (A1)
•	Relacionar imóvel através do nome/endereço da primeira coluna
•	Relacionar proprietários através dos nomes das colunas
•	Converter valores monetários (inclusive negativos)
•	Validar que soma dos valores individuais + taxa ≈ Valor Total
•	Permitir valores negativos (aluguéis não recebidos, ajustes)
Requisitos Técnicos
Tecnologias e Bibliotecas
•	Leitura de Excel: Utilizar biblioteca adequada (ex: SheetJS/xlsx, openpyxl, apache-poi, etc.)
•	Processamento: Manipular múltiplas planilhas em um mesmo arquivo
•	Validação: Implementar validações de integridade de dados
•	Transações: Garantir atomicidade na importação (tudo ou nada)
Interface do Usuário
•	Permitir seleção de múltiplos arquivos ou pasta
•	Indicar progresso da importação
•	Exibir log de erros e avisos
•	Confirmar dados antes de importar
•	Opção de rollback em caso de erro
Tratamento de Erros
•	Erros de formato: Arquivo corrompido, estrutura incorreta
•	Erros de validação: Dados inválidos, referências não encontradas
•	Erros de duplicação: Registros já existentes
•	Erros de relacionamento: Proprietário ou imóvel não encontrado
Ordem de Importação
1.	Primeiro: Proprietario.xlsx (criar registros de proprietários)
2.	Segundo: Imoveis.xlsx (criar registros de imóveis)
3.	Terceiro: Participacao.xlsx (criar relacionamentos proprietário-imóvel)
4.	Quarto: Aluguel.xlsx (criar registros de aluguéis mensais)
Validações Importantes
•	Verificar existência de colunas obrigatórias
•	Validar tipos de dados antes de inserir
•	Verificar integridade referencial (imóveis e proprietários devem existir)
•	Normalizar nomes para matching (trim, lowercase para comparação)
•	Validar somas e totais
•	Alertar sobre inconsistências sem bloquear importação
Funcionalidades Adicionais Desejáveis
•	Preview: Mostrar dados antes de importar
•	Modo atualização: Atualizar registros existentes ao invés de duplicar
•	Modo incremental: Importar apenas novos registros
•	Exportação de log: Salvar relatório da importação
•	Validação prévia: Validar arquivos antes de iniciar importação
•	Mapeamento flexível: Permitir ajustar nome de colunas se diferirem do padrão
Output Esperado
Após implementação, o sistema deve:
•	Processar todos os arquivos com sucesso
•	Apresentar relatório com quantidade de registros importados
•	Listar erros/avisos encontrados
•	Permitir reprocessamento de arquivos com erros corrigidos
•	Manter integridade referencial no banco de dados
Usar a BD existente
