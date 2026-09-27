# Refactor Race - Checkout

## DIAGNÓSTICO INICIAL

1. **A função `process_order` possui muitas responsabilidades.** Em ~120 linhas ela calcula subtotal, desconto, frete, imposto, pontos de fidelidade e duplicatas, além de imprimir e mutar estado global. Violação de SRP (Single Responsibility).
2. **Há duplicação de código.** O subtotal é calculado duas vezes (`legacy_checkout.py:9-18`), sendo `total1` descartado; `valor_com_desconto + frete + imposto` repete-se 3x (`:91-93,105`); a lista de estados MG/SP/RJ/ES aparece 2x (`:63,74-81`).
3. **Condicionais excessivamente aninhadas.** Desconto por cliente chega a 3 níveis de `if` (`:23-34`) e duplicados mais 3 (`:98-103`) — confirmado pelos 3 avisos SIM102 do Ruff.
4. **Números e strings mágicos.** Taxas (0.07–0.12), limites (500, 800, 1000), percentuais de desconto e cupons (`"PROMO10"`, `"VIP50"`) espalhados inline, sem constantes nomeadas.
5. **Nomes pouco descritivos e inconsistência pt/en.** `total1`, `x`; variáveis em português (`desconto`, `frete`) vs. chaves do resultado em inglês (`subtotal`, `shipping`).
6. **Estado global mutável.** `ORDERS_PROCESSED` (`:3,118`) gera efeito colateral e torna os testes não isolados.
7. **Baixa testabilidade.** `print()` no meio do cálculo (`:120-125`) e acoplamento a dicionários sem validação; entrada inválida → `KeyError` ou silêncio.