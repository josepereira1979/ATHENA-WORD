# ATHENA WORLD — Fase de Operação Global

## Estado

A branch \`world-intelligence-phase1\` contém a arquitectura para:

- WORLD CORE e relógio virtual;
- WORLD ORCHESTRATOR e WORLD RUNTIME;
- famílias e agentes;
- empresas virtuais;
- identidade canónica de empresas reais;
- listings e exchanges;
- ingestão/validação de empresas cotadas;
- censo global;
- distribuição 1:1 família → empresa real → empresa virtual;
- rede corporativa documentada;
- propagação de risco/oportunidade;
- fila de choques;
- previsões e validação contra observações;
- aprendizagem;
- painel de controlo e integridade.

## Regra fundamental

A WORLD não deve copiar o mercado real para dentro da simulação.

A realidade entra como observação/evidência.

A WORLD formula hipóteses e previsões próprias.

Depois compara:

1. o que a WORLD previu;
2. o que aconteceu na realidade;
3. onde acertou;
4. onde falhou;
5. porquê;
6. o que aprendeu.

## Comandos

A partir da raiz do projecto:

\`\`\`powershell
.venv\\Scripts\\python.exe -m world.run_world status
.venv\\Scripts\\python.exe -m world.run_world integrity
.venv\\Scripts\\python.exe -m world.run_world preview
.venv\\Scripts\\python.exe -m world.run_world sync-sec --user-agent "ATHENA WORLD contacto-real@exemplo.pt" --max-new 100
.venv\\Scripts\\python.exe -m world.run_world readiness
.venv\\Scripts\\python.exe -m world.run_world cycle --cycles 1
\`\`\`

\`status\` não avança o relógio.

\`integrity\` não avança o relógio.

\`preview\` não avança o relógio.

\`cycle\` avança explicitamente o mundo e executa os processadores registados.


`sync-sec` consulta a fonte pública de emissores da SEC e ingere identidades/listings. É necessário substituir o contacto de exemplo por um contacto real no `--user-agent`. O comando não atribui famílias automaticamente; primeiro verificar `preview`, `integrity` e `readiness`. Esta sincronização de emissores não equivale a um feed live de preços/eventos.

## Povoamento global

Antes de distribuir famílias, verificar:

\`\`\`text
global_world_status()
preview_global_world()
\`\`\`

A atribuição só deve ocorrer quando existir capacidade real suficiente.

Nunca criar empresas fictícias apenas para preencher as 1.001 famílias.

## Relações corporativas

As relações devem conter:

- empresa origem;
- empresa destino;
- tipo;
- confiança;
- estado;
- fonte;
- evidência;
- período de validade.

Relações inferidas devem continuar marcadas como INFERRED/PROBABLE e nunca ser apresentadas como factos confirmados.

## Sobrevivência e investigação familiar

Cada família mantém reservas de comida/água, saúde, energia, abrigo, ferramentas e nível de evolução. O Survival Engine consome recursos por ciclo. Recursos adicionais só podem ser desbloqueados por uma avaliação explícita com evidência e previsões validadas; observações sem validação não contam como sucesso. Os dados de sobrevivência são persistidos no estado da família, com compatibilidade retroactiva para estados antigos.

Os agentes recebem funções de investigação (ANALYST / CONTRARIAN) e contadores de evidência e previsões. O Reality Bridge regista a fonte declarada de cada observação; a etiqueta de uma fonte, por si só, não prova que exista uma sessão live.

## Estado da ligação ao mundo real

O adaptador actual não é uma ligação live. `connected=false` e `live_connection_verified=false` são os valores esperados até ser configurado e testado um fornecedor externo. `readiness` distingue prontidão estrutural de `live_data_ready`. Não anunciar a WORLD como ligada ao mercado apenas porque existem empresas/listings no universo.

## Princípio de segurança

A ATHENA WORLD não envia ordens de mercado.

A WORLD é uma camada de observação, simulação, investigação, previsão e aprendizagem.

Qualquer integração futura com decisão financeira deve passar por validação, risco e aprovação explícita fora deste runtime.
