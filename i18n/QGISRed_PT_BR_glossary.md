# QGISRed — Glossário de Tradução PT-BR (alinhado ao Manual EPANET 2.0 Brasil)

Fonte autoritativa: *Manual do Usuário EPANET 2.0 Brasil* (LENHS-UFPB).
Este glossário define a terminologia técnica de hidráulica usada para traduzir
`i18n/qgisred_pt.ts` para o **português do Brasil**.

> Os itens marcados com ⚠️ são **decisões de terminologia** com mais de uma forma
> válida — confirme a forma preferida antes da aplicação em massa.

---

## 1. Componentes da rede (objetos EPANET)

| Inglês (source) | PT-BR (EPANET Brasil) | Observação |
|---|---|---|
| Node | **Nó** | termo genérico (cap. 3.1.1) |
| Link | **Trecho** | termo genérico do EPANET Brasil |
| Junction ⚠️ | **Nó** *(ou “Junção”)* | manual chama o objeto de “Nó”; ver §6 |
| Reservoir ⚠️ | **Reservatório de Nível Fixo (RNF)** *(ou “Reservatório”)* | cap. 3.1.2; ver §6 |
| Tank ⚠️ | **Reservatório de Nível Variável (RNV)** *(ou “Tanque”)* | cap. 3.1.3; ver §6 |
| Pipe | **Tubulação** | cap. 3.1.5 |
| Pump | **Bomba** | cap. 3.1.7 |
| Valve | **Válvula** | cap. 3.1.8 |
| Emitter | **Emissor** / Dispositivo emissor | cap. 3.1.4 |
| Source | **Origem** (de qualidade) | |
| Demand (object/layer) ⚠️ | **Consumo** *(ou “Demanda”)* | manual usa “Consumo”; ver §6 |

### Tipos de válvula
| Source | PT-BR | Sigla |
|---|---|---|
| PRV (Pressure Reducing Valve) | Válvula Redutora de Pressão | VRP |
| PSV (Pressure Sustaining Valve) | Válvula Sustentadora de Pressão | VSP |
| PBV (Pressure Breaker Valve) | Válvula de Perda de Carga Fixa | — |
| FCV (Flow Control Valve) | Válvula Reguladora de Vazão | VRV |
| TCV (Throttle Control Valve) | Válvula de Controle de Perda de Carga | — |
| GPV (General Purpose Valve) | Válvula Genérica | — |

---

## 2. Propriedades hidráulicas e de qualidade

| Inglês (source) | PT-BR (EPANET Brasil) |
|---|---|
| Flow | **Vazão** *(nunca “Caudal”)* |
| Pressure | Pressão |
| Velocity | Velocidade |
| Head / Total Head | Carga hidráulica / Cota piezométrica |
| Head (reservoir level) | Nível de água |
| HeadLoss | Perda de carga |
| Unit HeadLoss | Perda de carga unitária |
| Elevation | **Cota** (do terreno / do fundo) |
| Diameter | Diâmetro |
| Length | Comprimento |
| Roughness / Roughness Coeff | Rugosidade / Coeficiente de rugosidade |
| Friction factor | Fator de atrito |
| Minor Loss / Loss Coefficient | Coeficiente de perda de carga singular |
| Demand / Base Demand | Consumo / Consumo base |
| Demand Pattern | Padrão de consumo |
| Demand Deficit | Déficit de consumo |
| Emitter Coefficient | Coeficiente do emissor |
| Emitter Flow | Vazão do emissor |
| Quality / Initial Quality | Qualidade / Qualidade inicial |
| Source Quality | Origem da qualidade |
| Bulk Coefficient | Coeficiente de reação no volume do escoamento |
| Wall Coefficient | Coeficiente de reação na parede |
| Reaction Rate | Taxa de reação |
| Setting (valve) | Parâmetro de controle |
| Initial Status / Status | Estado inicial / Estado |
| Pattern | Padrão (temporal) |
| Curve | Curva |
| Control | Controle |
| Energy | Energia |
| Power | Potência |
| Speed / Speed Pattern | Velocidade (regulação) / Padrão de velocidade |
| Efficiency Curve | Curva de rendimento |
| Energy Price / Price Pattern | Preço de energia / Padrão de preço |

### Reservatórios (RNV / tanques)
| Source | PT-BR |
|---|---|
| Initial Level | Nível inicial |
| Minimum Level | Nível mínimo |
| Maximum Level | Nível máximo |
| Volume / Volume Curve | Volume / Curva de volume |
| Mixing Model | Modelo de mistura |
| Mixing Fraction | Fração do volume (de mistura) |
| Overflow | Extravasamento |
| Spill / Tank Spill Flow | Extravasamento / Vazão de extravasamento |

---

## 3. Unidades (Anexo A do manual)

Siglas de unidade de vazão **permanecem inalteradas**: `CFS, GPM, MGD, IMGD, AFD,
LPS, LPM, MLD, CMH, CMD`. Quando o nome por extenso for traduzível:

| Source | PT-BR |
|---|---|
| liters/sec (LPS) | litros por segundo |
| Cubic meters/hour (CMH) | metros cúbicos por hora |
| Cubic meters/day (CMD) | metros cúbicos por dia |
| Gallons/min (GPM) | galões por minuto |
| Million gal/day (MGD) | milhões de galões por dia |
| Cubic feet/sec (CFS) | pés cúbicos por segundo |
| Meters | metros |
| Feet | pés |
| Millimeters | milímetros |
| Inches | polegadas |
| Meters water column (mca) | metros de coluna de água |

---

## 4. Termos de interface (genéricos)

| Source | PT-BR | Nota |
|---|---|---|
| File | **Arquivo** | *(BR; nunca “ficheiro”)* |
| Save | Salvar | *(nunca “gravar”)* |
| Open / Close | Abrir / Fechar | |
| Add / Delete / Remove | Adicionar / Excluir / Remover | |
| Run model / Analyze | Executar modelo / Analisar | |
| Layer | Camada | |
| Pattern editor | Editor de padrões | |
| Report | Relatório | |
| Settings / Options | Configurações / Opções | |
| Project | Projeto | |
| Background | Plano de fundo | |
| Label | Rótulo | |
| Default values | Valores predefinidos | |

---

## 5. Correções de português europeu → Brasil (já presentes no arquivo)

Estas formas existem hoje no `qgisred_pt.ts` e **serão substituídas**:

| Atual (PT-PT/ES) | Corrigir para (PT-BR) | Ocorrências |
|---|---|---|
| Caudal | **Vazão** | 6 |
| ficheiro / Ficheiro | arquivo / Arquivo | 2 |
| demandado (caudal ~) | demandado → *Vazão total demandada* | — |
| (qualquer “gravar”) | salvar | conferir |

---

## 6. Decisões de terminologia (confirmadas)

1. **Junction** → **Nó** (termo do manual, cap. 3.1.1).
2. **Reservoir** → **Reservatório** · **Tank** → **Tanque** (formas curtas).
3. **Demand** → **Consumo** (oficial EPANET Brasil: “Consumo Base”, “Padrão de Consumo”).
