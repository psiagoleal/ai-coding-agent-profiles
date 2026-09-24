<!-- Caminho relativo: docs/tickets/MT-2.md -->

# MT-2 — Skill de núcleo de cálculo C++/CMake

**Contexto.** 5 repositórios de cálculo (`LT-Ampacidade`, `LT-HIW`, `clima_db`, `datavault`, `neocad`) usam C++ com CMake e nenhuma skill cobre.

**Escopo**

- Gate de detecção lendo `CMakeLists.txt` (versão mínima, padrão C++).
- Estrutura, separação núcleo/ligação, e teste com CTest.
- Regras de numérico: comparação de ponto flutuante, unidade, determinismo.

**Critério de aceite.** A skill instala, o gate aprova pelo menos dois dos cinco repositórios e recusa um projeto sem CMake.

**Fora de escopo.** O que não estiver acima. Mudança de escopo vira ticket novo, não
crescimento deste.
