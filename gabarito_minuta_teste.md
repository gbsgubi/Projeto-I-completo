# Gabarito da Minuta de Teste

Este documento acompanha a minuta sintética (`minuta_teste.pdf` / `.html`) e lista o que está
**correto** e o que foi **plantado como erro**, para validar se a ferramenta de verificação
detecta os problemas esperados.

A minuta simula um caso no **JEF** (Juizado Especial Federal), com dois períodos especiais
requeridos: ruído (06/03/1997 a 31/12/2002) e calor (01/01/2003 a 18/11/2010).

---

## O que está CORRETO (a ferramenta deve aprovar)

| Item | Observação |
|------|-----------|
| Endereçamento | Correto para JEF ("JUIZADO ESPECIAL FEDERAL"), coerente com o nº do processo (...4.03.6183, subseção JEF) |
| NB, DER, processo, autor | Todos preenchidos |
| Preliminar Juízo 100% Digital | Presente, texto padrão |
| Preliminar Audiência de Conciliação | Presente, texto padrão |
| Preliminar Renúncia 60 SM | Presente e correta — o caso é no JEF, então deve constar |
| Calor — tese de limite | Correta: para 01/01/2003 a 18/11/2010 (período entre 06/03/1997 e 10/12/2019), o limiar de 25ºC é o aplicável |
| Calor — responsável técnico | Correto: exigível a partir de 14/10/1996 |
| Outros fundamentos | Vedação de conversão após 13/11/2019 — coerente (embora o período não ultrapasse, é fundamento padrão; não é erro grave) |

---

## ERROS PLANTADOS (a ferramenta deve reprovar / sinalizar)

### Erro 1 — Marcação amarela não removida `[ALTA PRIORIDADE]`
Há um trecho destacado em amarelo logo após a preliminar de decadência:
> "[VERIFICAR: deixar a preliminar de decadência somente quando contabilizar 10 anos...]"

**Esperado:** a ferramenta deve apontar que há anotação de edição não removida.
**Nota técnica:** no PDF o destaque amarelo vira texto comum; a detecção pode se dar pelo padrão
textual (colchetes, "VERIFICAR", instrução em primeira pessoa). No HTML, a classe `amarelo` permite
detecção direta.

### Erro 2 — Tese de ruído incorreta para o período `[ALTA PRIORIDADE]`
No período de **06/03/1997 a 31/12/2002**, a tese de limite de tolerância foi declarada como
"dentro do limite de tolerância - 90 dB(A)" de forma única. Porém esse período **cruza dois marcos
temporais** do ruído:
- 06/03/1997 a 02/12/1998 → limite de 90 dB(A)
- 03/12/1998 a 31/12/2002 → limite de 90 dB(A), mas a tese deve mencionar a exigência de NEN/
  metodologia conforme a MP 1.729/98

**Esperado:** sinalizar que a tese de ruído está incompleta para um período que abrange a fronteira
de 03/12/1998 — o tratamento de um único bloco de dB não cobre corretamente a transição.

### Erro 3 — Período de calor ultrapassa a data de emissão? `[VERIFICAR MANUALMENTE]`
O PPP foi emitido em 12/03/2019, mas o período de calor vai até 18/11/2010 — neste caso **não há**
erro (período é anterior à emissão). Item incluído de propósito para confirmar que a ferramenta
**não** gera falso positivo aqui.

### Erro 4 — Falta a preliminar de Prescrição `[MÉDIA PRIORIDADE]`
A minuta tem decadência, mas **não** tem a preliminar de prescrição. Considerando a DER (14/02/2022)
e uma ação ajuizada em 2024, há parcelas vencidas há mais de 5 anos? **Depende da data de
ajuizamento** — este é um caso de "verificar manualmente": a ferramenta deve perguntar/sinalizar a
ausência da prescrição para confirmação, não reprovar automaticamente.

### Erro 5 — Decadência possivelmente indevida `[VERIFICAR MANUALMENTE]`
A preliminar de decadência trata de **revisão** de benefício já concedido. Mas a ação é de
**concessão** de aposentadoria especial (não há benefício anterior a revisar, pelo que consta na
síntese). A decadência pode ser inaplicável aqui.

**Esperado:** sinalizar possível inconsistência entre o tipo de ação (concessão) e a preliminar de
decadência (que pressupõe ato de concessão anterior).

---

## Resumo do veredito esperado

| Bloco | Resultado esperado |
|-------|--------------------|
| Estrutural | **Erro** (marcação amarela não removida) |
| Preliminares | **Verificar** (prescrição ausente; decadência possivelmente indevida) |
| Agentes nocivos | **Erro** (tese de ruído incompleta na fronteira de 03/12/1998) |
| Averbação / pedidos | OK (não há pedidos acessórios neste caso) |
| Redistribuição | OK (sem vigilante/saúde) |

**Veredito final esperado: REPROVADO**, com 2 erros de alta prioridade e 3 pontos de verificação manual.

---

## Como usar este material

1. Use `minuta_teste.pdf` como entrada da ferramenta (simula o upload do estagiário).
2. Forneça como contexto adicional: juízo = JEF; data de ajuizamento = (definir, ex. 20/01/2024);
   PPP no PA = sim; análise técnica no PA = sim.
3. Compare o relatório gerado com o veredito esperado acima.
4. A versão `.html` permite testar também a extração a partir do formato nativo do SAPIENS.

> Observação: esta minuta é **inteiramente fictícia**, criada para teste. Nomes, números de
> processo, NB e datas são inventados. Os argumentos jurídicos foram baseados na estrutura do
> Manual 2024 e em peças públicas, mas a combinação é sintética.
