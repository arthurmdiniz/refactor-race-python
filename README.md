# Refactor Race - Checkout

## DIAGNÓSTICO INICIAL

1. **A função `process_order` possui muitas responsabilidades.** Em ~120 linhas ela calcula subtotal, desconto, frete, imposto, pontos de fidelidade e duplicatas, além de imprimir e mutar estado global. Violação de SRP (Single Responsibility).
2. **Há duplicação de código.** O subtotal é calculado duas vezes (`legacy_checkout.py:9-18`), sendo `total1` descartado; `valor_com_desconto + frete + imposto` repete-se 3x (`:91-93,105`); a lista de estados MG/SP/RJ/ES aparece 2x (`:63,74-81`).
3. **Condicionais excessivamente aninhadas.** Desconto por cliente chega a 3 níveis de `if` (`:23-34`) e duplicados mais 3 (`:98-103`) — confirmado pelos 3 avisos SIM102 do Ruff.
4. **Números e strings mágicos.** Taxas (0.07–0.12), limites (500, 800, 1000), percentuais de desconto e cupons (`"PROMO10"`, `"VIP50"`) espalhados inline, sem constantes nomeadas.
5. **Nomes pouco descritivos e inconsistência pt/en.** `total1`, `x`; variáveis em português (`desconto`, `frete`) vs. chaves do resultado em inglês (`subtotal`, `shipping`).
6. **Estado global mutável.** `ORDERS_PROCESSED` (`:3,118`) gera efeito colateral e torna os testes não isolados.
7. **Baixa testabilidade.** `print()` no meio do cálculo (`:120-125`) e acoplamento a dicionários sem validação; entrada inválida → `KeyError` ou silêncio.

## PRINCIPAIS REFATORAÇÕES

### 1. Separação das responsabilidades

**PROBLEMA ENCONTRADO:**

A função `process_order()` fazia praticamente tudo: calculava subtotal,
desconto, peso, frete, imposto, pontos e produtos duplicados.

**ALTERAÇÃO REALIZADA:**

Cada parte do processamento foi separada em uma função:

- `calculate_subtotal()`: calcula o subtotal dos itens validos do pedido;
- `calculate_discount()`: aplica o desconto do tipo de cliente e do cupom;
- `calculate_total_weight()`: calcula o peso total dos produtos;
- `calculate_shipping()`: calcula o frete normal, gratis ou express;
- `calculate_tax()`: calcula o imposto de acordo com o estado;
- `calculate_points()`: calcula os pontos de fidelidade do cliente;
- `find_duplicate_products()`: encontra produtos repetidos no pedido.

**JUSTIFICATIVA:**

As funções ficaram menores e cada uma passou a ter uma responsabilidade mais
especifica. Isso facilita a leitura, a manutenção e a criação de testes.

### 2. Remoção de código duplicado

**PROBLEMA ENCONTRADO:**

O subtotal era calculado duas vezes, e o primeiro resultado (`total1`) não era
utilizado.

**ALTERAÇÃO REALIZADA:**

O cálculo foi concentrado em `calculate_subtotal()` e passou a ser executado
uma única vez dentro de `process_order()`.

**JUSTIFICATIVA:**

Evita processamento desnecessário e reduz a possibilidade de os dois cálculos
ficarem com regras diferentes no futuro.

### 3. Simplificação das condicionais

**PROBLEMA ENCONTRADO:**

Havia condicionais aninhadas para verificar o tipo de cliente, o estado e as
regras de frete.

**ALTERAÇÃO REALIZADA:**

As regras foram reorganizadas nas funções de desconto e frete. A verificação
dos estados passou a usar o conjunto de estados existente em `TAX_RATES`, e as
taxas de imposto passaram a ser obtidas com `TAX_RATES.get()`.

**JUSTIFICATIVA:**

O fluxo ficou mais direto e a inclusão ou alteração de um estado exige menos
mudanças no código.

### 4. Organização das constantes

**PROBLEMA ENCONTRADO:**

Taxas, limites, valores de frete, descontos e cupons ficavam misturados com a
lógica do processamento.

**ALTERAÇÃO REALIZADA:**

Essas regras foram declaradas no início do arquivo e agrupadas por categoria:

- taxas de imposto;
- valores do frete;
- descontos;
- cupons;
- regras de pontos de fidelidade.

**JUSTIFICATIVA:**

Fica mais fácil localizar e alterar uma regra sem precisar procurar valores
espalhados pelo código.

### 5. Separação da saída do processamento

**PROBLEMA ENCONTRADO:**

`process_order()` imprimia informações do pedido enquanto realizava os
cálculos. Isso misturava a lógica de negócio com a saída no terminal.

**ALTERAÇÃO REALIZADA:**

Os `print()` foram retirados do processamento. A função agora monta e retorna o
dicionário com os dados do pedido.

**JUSTIFICATIVA:**

O resultado fica mais fácil de testar e pode ser usado por outras partes do
sistema sem gerar mensagens no terminal automaticamente.

No final, `process_order()` ficou responsável por organizar o processamento.
Ela chama cada função na ordem necessária, junta os valores, monta o resultado
final, registra o pedido e devolve o dicionário esperado.

