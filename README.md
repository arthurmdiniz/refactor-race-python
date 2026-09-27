# Refactor Race - Python

## EQUIPE

- **Integrante 1** - Arthur Marques Diniz - RA: 42520344
- **Integrante 2** - Bernardo Luiz Monteverde Gonçalves - RA: 4251923322
- **Integrante 3** - Luiz Filipe Pimenta Correa - RA: 4261214196
- **Integrante 4** - Patrick Oliveira Rabelo de Brito - RA: 4251923386

## DESCRIÇÃO

O projeto consiste em refatorar o módulo legado `src/legacy_checkout.py`, que
implementa o processamento de pedidos de um checkout. A função `process_order()`
recebe o cliente, a lista de itens, um cupom opcional, o estado de entrega e a
flags de frete expresso, e devolve um dicionário com subtotal, desconto, frete,
imposto, total, pontos de fidelidade e produtos duplicados.

O objetivo da refatoração foi reorganizar o código aplicando técnicas de
refatoração, **sem alterar o contrato público** de `process_order()`: a
assinatura e as oito chaves do dicionário retornado foram mantidas exatamente
como estavam. A métrica de referência é a cobertura de testes, que subiu de 83%
para 100%, acompanhada da redução da complexidade ciclomática de E (34) para
A (1) na função principal.

## DIAGNÓSTICO INICIAL

1. **A função `process_order` possui muitas responsabilidades.** Em ~120 linhas
   ela calcula subtotal, desconto, frete, imposto, pontos de fidelidade e
   duplicatas, além de imprimir e mutar estado global. Violação de SRP
   (Single Responsibility Principle).
2. **Há duplicação de código.** O subtotal era calculado duas vezes, sendo o
   primeiro resultado (`total1`) descartado; a expressão
   `valor_com_desconto + frete + imposto` repetia-se três vezes; a lista de
   estados MG/SP/RJ/ES aparecia duas vezes.
3. **Condicionais excessivamente aninhadas.** O desconto por cliente chegava a
   três níveis de `if` e a busca de duplicados mais três, o que foi confirmado
   pelos três avisos SIM102 do Ruff.
4. **Números e strings mágicos.** Taxas (0.07 a 0.12), limites (500, 800,
   1000), percentuais de desconto e cupons (`"PROMO10"`, `"VIP50"`) espalhados
   inline, sem constantes nomeadas.
5. **Nomes pouco descritivos e inconsistência pt/en.** `total1`, `x`; variáveis
   em português (`desconto`, `frete`) contra chaves do resultado em inglês
   (`subtotal`, `shipping`).
6. **Estado global mutável.** `ORDERS_PROCESSED` gerava efeito colateral e
   tornava os testes não isolados.
7. **Baixa testabilidade.** Havia `print()` no meio do cálculo e acoplamento a
   dicionários sem validação; entrada inválida resultava em `KeyError` ou em
   silêncio.

## CODE SMELLS ENCONTRADOS

| Code smell | Onde estava | Consequência |
|---|---|---|
| Função longa | `process_order` com ~120 linhas | Setas de controle demais, difícil de revisar e testar |
| Falta de coesão / SRP | Cálculo, validação, impressão e persistência na mesma função | Uma alteração em regra de frete quebra o cálculo de impostos |
| Código duplicado | Subtotal calculado duas vezes; `total1` nunca usado; total repetido 3x; UFs repetidas 2x | Processamento desperdiçado e risco de as duas versões divergirem |
| Condicional aninhada | 3 níveis de `if` no desconto e na busca de duplicados | Complexidade ciclomática E (34); 3 avisos SIM102 |
| Número mágico | 0.07, 0.12, 500, 800, 1000, 0.25, `"PROMO10"` | Regra de negócio escondida dentro de expressões |
| Nomenclatura enganosa | `total1`, `x`, `produto` para o mesmo conceito | Leitura exige abrir o arquivo para descobrir o que a variável guarda |
| Inconsistência de idioma | Variáveis em pt/en misturados | Reforça o problema 5 do diagnóstico |
| Estado global | `ORDERS_PROCESSED`appendado a cada chamada | Efeito colateral invisível, testes dependem de ordem de execução |
| Acoplamento a entrada | Acesso direto a `customer["type"]` e `item["price"]` sem validação | `KeyError` em vez de erro de domínio |
| Efeito colateral de saída | `print()` no meio do cálculo | Teste precisa capturar stdout; polui o uso como biblioteca |

## REFATORAÇÕES REALIZADAS

### 1. Extract Function (separação de responsabilidades)

**Problema:** `process_order()` calculava subtotal, desconto, peso, frete,
imposto, pontos e duplicatas em um único bloco.

**Alteração:** cada regra virou uma função com uma responsabilidade:

- `calculate_subtotal()` - soma `price * qty` dos itens com quantidade positiva;
- `calculate_discount()` - desconto por tipo de cliente e por cupom, com teto;
- `calculate_total_weight()` - peso total, usando `weight` ausente como 0;
- `calculate_shipping()` - frete normal, grátis ou expresso;
- `calculate_tax()` - imposto a partir da taxa do estado;
- `calculate_points()` - pontos de fidelidade (divisor 5 para VIP, 10 nos demais);
- `find_duplicate_products()` - produtos repetidos, preservando a ordem de
  primeira aparição.

**Justificativa:** `process_order()` passou a orquestrar: chamar, juntar, montar o
resultado, registrar e devolver. Cada regra pode ser testada isoladamente.

### 2. Remoção de código duplicado

**Problema:** o subtotal era calculado duas vezes e `total1` era descartado;
`valor_com_desconto + frete + imposto` aparecia três vezes.

**Alteração:** o cálculo ficou em `calculate_subtotal()`, executado uma única
vez, e a soma do total foi calculada uma vez em `process_order()`.

**Justificativa:** elimina processamento desnecessário e impede que as duas
cópias do cálculo evoluam para regras diferentes.

### 3. Replace Conditional with Mapping

**Problema:** a taxa de imposto era escolhida por uma cadeia de quatro `elif`
comparando cada estado, e a lista de estados do Sudeste aparecia duplicada.

**Alteração:** as taxas passaram a ser obtidas por `TAX_RATES.get(state,
DEFAULT_TAX_RATE)` e o frete passou a testar `state in TAX_RATES`.

**Justificativa:** incluir, remover ou alterar um estado passa a exigir a
edição de uma única linha, e as duas listas duplicadas foram eliminadas.

### 4. Simplificação de condicionais

**Problema:** três níveis de `if` aninhados no desconto por cliente e na busca
de duplicados.

**Alteração:** o desconto virou uma cadeia `if/elif` com ternário no caso VIP;
a busca de duplicados virou uma contagem por dicionário, e o teto de desconto
virou `min(discount, subtotal * MAX_DISCOUNT_RATE)`.

**Justificativa:** eliminou os três avisos SIM102 e o PLR1730, e trocou a busca
O(n²) de pares por uma contagem O(n).

### 5. Replace Magic Number with Constant

**Problema:** taxas, limites, percentuais e cupons estavam inline.

**Alteração:** cerca de 30 constantes nomeadas foram declaradas no topo do
arquivo, agrupadas por categoria: taxas de imposto, valores de frete,
descontos, cupons e pontos de fidelidade.

**Justificativa:** a regra de negócio fica localizada e ajustável sem caça ao
número dentro de expressões.

### 6. Remoção dos `print()`

**Problema:** `process_order()` imprimia o resumo do pedido durante o cálculo.

**Alteração:** as impressões foram removidas; a função monta e devolve o
dicionário.

**Justificativa:** separa a lógica de negócio da saída em terminal e elimina a
necessidade de capturar stdout nos testes.

### 7. Padronização da nomenclatura

**Problema:** `total1`, `x`, e a mistura de português e inglês.

**Alteração:** variáveis, parâmetros e nomes de função passaram a inglês
(`subtotal`, `discount`, `shipping`, `total_weight`), alinhados às chaves do
dicionário retornado.

**Justificativa:** elimina a inconsistência apontada no item 5 do diagnóstico e
alinha o código ao contrato público, que já é em inglês.

## TESTES ADICIONADOS

A suíte foi ampliada de 4 para 12 testes, cobrindo 100% das linhas de
`src/legacy_checkout.py`. Os oito testes novos:

| Teste | Cenário coberto |
|---|---|
| `test_funcionario` | Cliente `employee` recebe 20% de desconto; cobre o ramo antes não exercitado de `calculate_discount` |
| `test_fretegratis` | Frete grátis no limiar exato de 500, com imposto por estado (RJ) |
| `test_desconto_25_por_cento` | Teto de 25% atingido: 20% de employee + 10% de PROMO10 = 30%, limitado a 150,00 |
| `test_desconto_exatamente_no_limite` | 15% de VIP + 10% de PROMO10 = 25% exatos, que não devem ser reduzidos |
| `test_desconto_com_cupom` | Cupom de valor fixo (VIP50) em pedido VIP, também limitado pelo teto |
| `test_cupom_promo20` | Cupom PROMO20 válido (subtotal acima do mínimo de 500) |
| `test_frete_fora_do_sudeste` | Estado fora de `TAX_RATES` (BA): tabela de frete alternativa e imposto de 12% |
| `test_frete_expresso` | `express=True` anula o frete grátis e multiplica o valor por 1,8 |

Os quatro testes originais (`test_regular_customer`, `test_vip_customer`,
`test_coupon`, `test_duplicate_products`) foram preservados sem alteração,
funcionando como verificação de que a refatoração não quebrou o comportamento
esperado.

## MÉTRICAS ANTES E DEPOIS

| Indicador | Antes | Depois |
|---|---|---|
| Testes passando | 4 passed | 12 passed |
| Cobertura de testes | 83% (12/72 linhas sem teste) | 100% (0/80 linhas sem teste) |
| Complexidade da função principal | E (34) | A (1) - `process_order` |
| Complexidade média | E (34.0) | A (3.6) - 8 blocos |
| Complexidade mais alta do módulo | E (34) | C (11) - `calculate_discount` |
| Índice de manutenibilidade | A (51.69) | A (48.60) |
| Problemas identificados pelo Ruff | 4 (3x SIM102, 1x PLR1730) | 0 (`All checks passed!`) |
| Quantidade de testes | 4 | 12 |
| Linhas de código (LOC) | 127 | 141 |

**Sobre a queda do índice de manutenibilidade (51.69 para 48.60):** o Radon
calcula esse índice a partir do volume de Halstead, da complexidade total e do
número de linhas. A extração das sete funções e a declaração de cerca de 30
constantes aumentaram o LOC de 127 para 141, e esse crescimento é penalizado
pela fórmula. A nota permanece na classe A e a complexidade ciclomática - que
mede a dificuldade real de entender os caminhos de execução - caiu de E (34)
para A (1). Ou seja, o código está mais legível; o índice apenas reage ao
tamanho do arquivo.

**Como reproduzir as medições:**

```powershell
# na raiz do repositório
pytest --cov=legacy_checkout --cov-report=term-missing

# dentro de src\
radon cc legacy_checkout.py -s -a
radon mi legacy_checkout.py -s
ruff check legacy_checkout.py --statistics
```

O `pytest` precisa ser executado na raiz, porque o `pyproject.toml` define
`testpaths = ["tests"]`. O Radon e o Ruff são executados em `src\`, onde o
módulo está localizado; rodá-los na raiz resulta em erro de arquivo não
encontrado (`E902`) e em `collected 0 items`.

## DECISÕES TÉCNICAS

1. **Preservar o contrato público.** A assinatura de `process_order()` e as
   oito chaves do dicionário retornado não foram alteradas, conforme exigido
   pelo enunciado. Nenhum teste original precisou ser adaptado.
2. **Manter o global `ORDERS_PROCESSED`.** Ele é observável por quem consome o
   módulo, portanto foi preservado apesar de ser um efeito colateral. A remoção
   foi registrada como melhoria futura, não realizada agora.
3. **Frete grátis calculado sobre o subtotal antes do desconto.** O código
   original já usava o subtotal, e isso foi mantido de propósito: o desconto é
   aplicado depois de decidir o frete. Os testes `test_fretegratis` e
   `test_desconto_com_cupom` fixam esse comportamento.
4. **Reaproveitar `TAX_RATES` como conjunto do Sudeste.** A regra de frete
   (`20 + peso * 0.4`) e a regra de imposto (taxa por estado) compartilham a
   mesma lista de estados do Southeast. Usar `state in TAX_RATES` nos dois
   lugares eliminou a duplicação sem introduzir uma segunda lista que poderia
   divergir.
5. **Cúpons como `if/elif` em vez de soma cumulative.** O original somava
   cupons em `if` independentes. A versão nova usa `elif`, o que garante que
   apenas um cupom seja aplicado por pedido, mantendo o comportamento prático
   para quem usa cupons válidos.
6. **Nomenclatura em inglês.** Nomes de função, parâmetros e variáveis seguem o
   idioma das chaves públicas, eliminando a mistura pt/en apontada no
   diagnóstico.
7. **Nenhuma alteração em `BASELINE - NÃO ALTERAR`.** O arquivo de referência
   foi mantido intacto.

## USO DE INTELIGÊNCIA ARTIFICIAL

- **Ferramenta utilizada:**
  - GitHub Copilot (integrada ao VSCode).

- **Finalidade:**
  - Complementar trechos de codigo por meio da sugestao exibida ao pressionar a tecla Tab.
  - Transformar e organizar textos em formato Markdown.
  - Ajudar a entender os erros apresentados durante a execucao dos testes e a identificar possiveis ajustes no codigo.
  - Adequação ao tópico 45 - README OBRIGATÓRIO.

- **Exemplo de sugestao recebida:**
  - Completar um trecho de codigo durante a digitacao.
  - Organizar uma explicacao em secoes e listas no README.md.
  - Apoiar a analise das mensagens de erro apresentadas pelo pytest e pelo Ruff.

- **A sugestao foi aceita, modificada ou rejeitada?**
  - A sugestao foi revisada antes de ser utilizada.
  - O texto em Markdown foi ajustado para ficar de acordo com o que foi realizado (era texto livre e foi formatado em Markdown, conforme estrutura do tópicos existente no PDF da atividade).

- **Como a equipe validou a solucao?**
  - Revisao do codigo.
  - Execucao dos testes automatizados com pytest.
  - Os testes foram executados novamente depois dos ajustes e passaram.
  - A execucao mais recente registrou 12 testes passando e 100% de cobertura.
  - Execucao do Ruff para verificar o lint.
  - Execucao do Radon para analisar a complexidade e a manutenibilidade.
  - A assinatura de process_order() e as chaves do dicionario retornado foram mantidas.

## MELHORIAS FUTURAS

1. **Eliminar o estado global `ORDERS_PROCESSED`.** O efeito colateral ainda
   existe. As opções são devolver o histórico, injetar um acumulador ou usar um
   `logging` dedicado.
2. **Validar a entrada.** Hoje um item sem `price` ou um cliente sem `type`
   levanta `KeyError`. Um validador no início de `process_order()` deveria
   emitir um erro de domínio explícito.
3. **Teste de contrato das chaves.** Nenhum teste garante que o dicionário
   retornado tem exatamente as oito chaves esperadas; um `assert set(result) ==
   {...}` impediria regressão silenciosa.
4. **Cenários que a cobertura de linha não captura.** A cobertura está em
   100%, mas faltam testes para: VIP abaixo de 1000 (taxa de 10%), PROMO20 com
   subtotal abaixo de 500 (ignorado), cupom inválido ou com caixa diferente
   (`"promo10"`), item sem a chave `weight`, item com `qty` zero ou negativa e
   a ordem de saída dos duplicados.
5. **Testes unitários das funções extraídas.** Hoje todos os 12 testes exercitam
   `process_order()`. Como as sete funções são públicas no módulo, vale cobri-las
   diretamente e assim isolar a origem de cada falha.
6. **Agrupar as constantes.** Encapsular as cerca de 30 constantes em um
   `dataclass` ou namespace reduziria o LOC e recuperaria parte do índice de
   manutenibilidade, sem voltar a espalhar números mágicos.
7. **Organizar o arquivo de saída.** Existe um arquivo `pytest` vazio (0 bytes)
   na raiz do repositório, criado provavelmente por um redirecionamento
   acidental de comando, e ele deve ser removido.
