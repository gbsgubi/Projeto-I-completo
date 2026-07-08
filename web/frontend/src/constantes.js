// Aparência por status — ERRO vermelho, VERIFICAR âmbar, INFO azul, OK verde.
// Regra de acessibilidade: status nunca é só cor — todo badge carrega glifo +
// rótulo, e os números dos contadores ficam em tinta neutra (texto), não na
// cor da série.

export const CORES_GRIFO = {
  ERRO: "rgba(220, 38, 38, 0.35)",
  VERIFICAR: "rgba(217, 119, 6, 0.35)",
  INFO: "rgba(37, 99, 235, 0.30)",
};

export const BORDAS_GRIFO = {
  ERRO: "rgba(220, 38, 38, 0.8)",
  VERIFICAR: "rgba(217, 119, 6, 0.8)",
  INFO: "rgba(37, 99, 235, 0.7)",
};

export const CLASSES_BADGE = {
  ERRO: "bg-red-100 text-red-800 border-red-300",
  VERIFICAR: "bg-amber-100 text-amber-800 border-amber-300",
  OK: "bg-green-100 text-green-800 border-green-300",
  INFO: "bg-blue-100 text-blue-800 border-blue-300",
};

// glifo que acompanha cada badge de status (nunca cor sozinha)
export const GLIFO_STATUS = {
  ERRO: "✕",
  VERIFICAR: "!",
  OK: "✓",
  INFO: "i",
};

// ponto colorido dos contadores e das legendas
export const PONTO_STATUS = {
  ERRO: "bg-red-500",
  VERIFICAR: "bg-amber-500",
  OK: "bg-green-500",
  INFO: "bg-blue-500",
};

// acento na borda esquerda dos itens do painel
export const ACENTO_ITEM = {
  ERRO: "border-l-red-400",
  VERIFICAR: "border-l-amber-400",
  OK: "border-l-green-300",
  INFO: "border-l-slate-200",
};
