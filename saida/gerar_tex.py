# -*- coding: utf-8 -*-
"""Gera resultado_contestacao_NN.tex a partir dos JSON do verificador,
seguindo o mesmo template de resultado_contestacao1/2/3.tex."""
import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(BASE, "out")
DEST = os.path.dirname(BASE)  # raiz do projeto

NUMS = ["03","04","05","06","07","08","09","10","11","12","13","14","15","16"]

# nomes das preliminares na ordem da tabela -> id no json
PRELIMS = [
    ("Juízo 100\\% Digital",                          "2.presenca:juizo-digital"),
    ("Audiência de Conciliação",                       "2.presenca:conciliacao"),
    ("Renúncia aos 60 Salários-Mínimos",               "2.presenca:renuncia-60sm"),
    ("Decadência",                                     "2.presenca:decadencia"),
    ("Prescrição",                                     "2.presenca:prescricao"),
    ("Coisa Julgada",                                  "2.presenca:coisa-julgada"),
    ("Litispendência",                                 "2.presenca:litispendencia"),
    ("PPP não apresentado administrativamente",        "2.presenca:ppp-nao-apresentado"),
    ("Períodos reconhecidos administrativamente",      "2.presenca:periodos-reconhecidos"),
    ("Petição inicial inepta",                         "2.presenca:inicial-inepta"),
]

def esc(s):
    """Escapa caracteres especiais do LaTeX em texto corrido."""
    if s is None:
        return ""
    s = s.replace("\\", "\\textbackslash{}")
    for a, b in [("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"),
                 ("_", "\\_"), ("{", "\\{"), ("}", "\\}"), ("~", "\\textasciitilde{}"),
                 ("^", "\\textasciicircum{}")]:
        s = s.replace(a, b)
    # travessão unicode usado nas mensagens do verificador
    s = s.replace("—", "---")
    return s

def ev(s):
    """Formata evidência: remove o '...' inicial (o template já o adiciona) e
    o lixo de pontuação antes da primeira letra; escapa para LaTeX."""
    if not s:
        return ""
    s = s.strip()
    if s.startswith("..."):
        s = s[3:]
    # remove pontuação/espaços à esquerda até a primeira letra/dígito
    s = re.sub(r"^[^0-9A-Za-zÀ-ÿ]+", "", s)
    return esc(s)

def by_id(vs, _id):
    for v in vs:
        if v["id"] == _id:
            return v
    return None

def find(vs, prefix):
    for v in vs:
        if v["id"].startswith(prefix):
            return v
    return None

def header_fields(vs):
    """Extrai nome do autor, processo, NB e DER das evidências."""
    autor = "—"
    va = by_id(vs, "1.2-campos-obrigatorios:nome-do-autor")
    if va and va.get("evidencia"):
        m = re.search(r"que lhe move (.+?), vem", va["evidencia"])
        if m:
            autor = m.group(1).strip()
    proc = nb = der = "—"
    vp = by_id(vs, "1.2-campos-obrigatorios:numero-do-processo")
    if vp and vp.get("evidencia"):
        m = re.search(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", vp["evidencia"])
        if m:
            proc = m.group(1)
    vn = by_id(vs, "1.2-campos-obrigatorios:nb")
    if vn and vn.get("evidencia"):
        m = re.search(r"NB: ([\d./\-]+)", vn["evidencia"])
        if m:
            nb = m.group(1)
    vd = by_id(vs, "1.2-campos-obrigatorios:der")
    if vd and vd.get("evidencia"):
        m = re.search(r"DER: ([\d/]+)", vd["evidencia"])
        if m:
            der = m.group(1)
    return autor, proc, nb, der

def status_cmd(status, texto):
    m = {"OK": "statusOK", "ERRO": "statusERRO",
         "INFO": "statusINFO", "VERIFICAR": "statusVERIFICAR"}[status]
    return "\\%s{%s}" % (m, texto)

TEMPLATE_HEAD = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[brazil]{babel}
\usepackage[margin=2.5cm]{geometry}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{parskip}
\usepackage{fancyhdr}
\usepackage{titlesec}

\definecolor{corOK}{HTML}{1a7a3c}
\definecolor{corERRO}{HTML}{c0392b}
\definecolor{corINFO}{HTML}{2471a3}
\definecolor{corVERIFICAR}{HTML}{d68910}
\definecolor{corFundoReprovado}{HTML}{fadbd8}
\definecolor{corFundoAprovado}{HTML}{d5f5e3}
\definecolor{cinzaClaro}{HTML}{f2f3f4}

\newcommand{\statusOK}[1]{\textcolor{corOK}{\textbf{[OK]}} #1}
\newcommand{\statusERRO}[1]{\textcolor{corERRO}{\textbf{[ERRO]}} #1}
\newcommand{\statusINFO}[1]{\textcolor{corINFO}{\textbf{[INFO]}} #1}
\newcommand{\statusVERIFICAR}[1]{\textcolor{corVERIFICAR}{\textbf{[VERIFICAR]}} #1}

\pagestyle{fancy}
\fancyhf{}
\rhead{Verificador de Contestação -- Fase 1}
\lhead{Contestação @@NUM@@}
\rfoot{Página \thepage}
\lfoot{Gerado em 07/07/2026}

\titleformat{\section}{\large\bfseries}{}{0em}{}[\titlerule]
\titleformat{\subsection}{\normalsize\bfseries}{}{0em}{}

\begin{document}

% -----------------------------------------------------------------------
% Cabeçalho
% -----------------------------------------------------------------------
\begin{center}
  {\LARGE \textbf{Relatório de Verificação de Contestação}}\\[0.4em]
  {\large Contestação @@NUM@@ --- @@AUTOR@@}\\[0.2em]
  {\small Processo n.º @@PROC@@ \quad NB: @@NB@@ \quad DER: @@DER@@}
\end{center}

\vspace{0.5em}
"""

def veredito_box(veredito, erros):
    if veredito == "REPROVADO":
        fundo, cor = "corFundoReprovado", "corERRO"
    else:
        fundo, cor = "corFundoAprovado", "corOK"
    return (
        "\\noindent\\colorbox{%s}{%%\n"
        "  \\begin{minipage}{\\dimexpr\\linewidth-2\\fboxsep}\n"
        "    \\centering\n"
        "    \\vspace{0.3em}\n"
        "    {\\large \\textcolor{%s}{\\textbf{VEREDITO: %s}}}\\\\\n"
        "    Erros: \\textbf{%d} \\quad|\\quad Pontos de verificação manual: \\textbf{0}\n"
        "    \\vspace{0.3em}\n"
        "  \\end{minipage}%%\n"
        "}\n\n\\vspace{1em}\n\n" % (fundo, cor, veredito, erros)
    )

def bloco1(vs):
    out = ["% -----------------------------------------------------------------------",
           "% Bloco 1 - Estrutural",
           "% -----------------------------------------------------------------------",
           "\\section{Bloco 1 --- Estrutural}", ""]
    # 1.1 endereçamento
    v = by_id(vs, "1.1-enderecamento")
    out.append(status_cmd("INFO", "Tipo de endereçamento (JEF x Justiça Federal comum)") + "\\\\")
    msg = v["mensagem"]
    if "JEF" in msg and "sem menção" not in msg:
        out.append("Endereçamento identificado: \\textbf{JEF (Juizado Especial Federal)}.\\\\")
    else:
        out.append("Endereçamento identificado: \\textbf{Justiça Federal comum (sem menção a JEF)}.\\\\")
    out.append("\\textit{Evidência: ... %s}" % ev(v["evidencia"]))
    out.append("")
    # campos obrigatórios
    campos = [
        ("nb", "NB"),
        ("der", "DER"),
        ("numero-do-processo", "Número do processo"),
        ("nome-do-autor", "Nome do autor"),
        ("tipo-de-beneficio", "Tipo de benefício"),
    ]
    for suf, rot in campos:
        v = by_id(vs, "1.2-campos-obrigatorios:" + suf)
        out.append("\\medskip")
        if v["status"] == "OK":
            linha = status_cmd("OK", "Campo obrigatório: %s" % rot) + " --- %s" % esc(v["mensagem"])
            if suf == "nome-do-autor" and v.get("evidencia"):
                linha += "\\\\\n\\textit{Evidência: ... %s}" % ev(v["evidencia"])
            out.append(linha)
        else:
            out.append(status_cmd("ERRO", "Campo obrigatório: %s" % rot) + "\\\\")
            out.append("\\textbf{%s}" % esc(v["mensagem"]))
        out.append("")
    # 1.3 marcações
    v = by_id(vs, "1.3-marcacoes-edicao")
    out.append("\\medskip")
    if v["status"] == "OK":
        out.append(status_cmd("OK", "Marcações de edição não removidas (colchetes, placeholders, instruções, amarelo)") + "\\\\")
        out.append("Nenhuma marcação de edição remanescente detectada.")
    else:
        out.append(status_cmd("ERRO", "Marcações de edição não removidas (colchetes, placeholders, instruções, amarelo)") + "\\\\")
        out.append("%s\\\\" % esc(v["mensagem"]))
        out.append("\\textit{Evidência: %s}" % ev(v["evidencia"]))
    out.append("")
    return "\n".join(out)

def bloco2(vs):
    out = ["% -----------------------------------------------------------------------",
           "% Bloco 2 - Preliminares",
           "% -----------------------------------------------------------------------",
           "\\section{Bloco 2 --- Preliminares (presença)}", "",
           "\\begin{longtable}{p{8.5cm} p{4.5cm}}",
           "  \\toprule",
           "  \\textbf{Preliminar} & \\textbf{Status} \\\\",
           "  \\midrule",
           "  \\endfirsthead",
           "  \\toprule",
           "  \\textbf{Preliminar} & \\textbf{Status} \\\\",
           "  \\midrule",
           "  \\endhead"]
    for rot, _id in PRELIMS:
        v = by_id(vs, _id)
        presente = v["mensagem"].strip().upper().startswith("PRESENTE")
        if presente:
            st = "\\textcolor{corOK}{\\textbf{PRESENTE}}"
        else:
            st = "AUSENTE"
        out.append("  %-45s & %s \\\\" % (rot, st))
    out.append("  \\bottomrule")
    out.append("\\end{longtable}")
    out.append("")
    # regra 2.3 renúncia JEF
    v = by_id(vs, "2.3-renuncia-jef")
    if v["status"] == "OK":
        out.append(status_cmd("OK", "Renúncia aos 60 SM obrigatória quando o juízo é o JEF") + "\\\\")
        out.append("Processo no JEF e preliminar de Renúncia aos 60 SM presente.")
    elif v["status"] == "ERRO":
        out.append(status_cmd("ERRO", "Renúncia aos 60 SM obrigatória quando o juízo é o JEF") + "\\\\")
        out.append("%s" % esc(v["mensagem"]))
    else:
        out.append(status_cmd("INFO", "Renúncia aos 60 SM obrigatória quando o juízo é o JEF") + "\\\\")
        out.append("%s" % esc(v["mensagem"]))
    out.append("")
    return "\n".join(out)

def bloco6(vs):
    out = ["% -----------------------------------------------------------------------",
           "% Bloco 6 - Redistribuição",
           "% -----------------------------------------------------------------------",
           "\\section{Bloco 6 --- Redistribuição}", ""]
    itens = [
        ("6.1-vigilante", "Indício de categoria vigilante/vigia/guarda/policial", "VIGILANTE"),
        ("6.2-saude", "Indício de profissional/ambiente de saúde + agente biológico", "SAÚDE"),
        ("6.3-professor", "Indício de professor com período posterior a 1981", "PROFESSOR"),
    ]
    for i, (_id, desc, flag) in enumerate(itens):
        v = by_id(vs, _id)
        if i > 0:
            out.append("\\medskip")
        if v["status"] == "OK":
            out.append(status_cmd("OK", desc) + " --- Sem indício detectado.")
        else:
            # flag de redistribuição sugerida
            out.append(status_cmd("INFO", desc) + "\\\\")
            det = esc(v["mensagem"]).replace("Redistribuição sugerida --- flag %s " % flag, "")
            out.append("\\textcolor{corVERIFICAR}{\\textbf{Redistribuição sugerida --- flag %s}} %s" % (flag, det))
            if v.get("evidencia"):
                out.append("\\\\\n\\textit{Evidência: %s}" % ev(v["evidencia"]))
        out.append("")
    return "\n".join(out)

TESES = r"""% -----------------------------------------------------------------------
% Teses
% -----------------------------------------------------------------------
\section{Teses presentes (Blocos 3/4/5 --- catalogação)}

\statusINFO{Catalogação das teses padronizadas presentes (CTN-/DIVESP- etc.)}\\
Nenhuma tese padronizada (CTN-/DIVESP-) encontrada no texto.
"""

ADIADAS = r"""% -----------------------------------------------------------------------
% Verificações adiadas
% -----------------------------------------------------------------------
\section{Verificações adiadas para a fase do LLM}

\begin{itemize}
  \item \texttt{[3.x]} Compatibilidade tese × agente × período (marcos temporais)
  \item \texttt{[2.8]} Distinção entre as três situações de PPP não apresentado
  \item \texttt{[2.45]} Cabimento de decadência/prescrição com base em datas e tipo de ação
  \item \texttt{[1.4]} Cobertura dos períodos requeridos na petição inicial
\end{itemize}

\end{document}
"""

for num in NUMS:
    with open(os.path.join(OUT_JSON, "contestacao_%s.json" % num), encoding="utf-8") as f:
        data = json.load(f)
    vs = data["verificacoes"]
    autor, proc, nb, der = header_fields(vs)
    parts = []
    head = (TEMPLATE_HEAD.replace("@@NUM@@", num).replace("@@AUTOR@@", esc(autor))
            .replace("@@PROC@@", proc).replace("@@NB@@", nb).replace("@@DER@@", der))
    parts.append(head)
    parts.append(veredito_box(data["veredito"], data["total_erros"]))
    parts.append(bloco1(vs))
    parts.append(bloco2(vs))
    parts.append(bloco6(vs))
    parts.append(TESES)
    parts.append(ADIADAS)
    tex = "\n".join(parts)
    dest = os.path.join(DEST, "resultado_contestacao_%s.tex" % num)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(tex)
    print("gerado:", dest)
print("OK")
