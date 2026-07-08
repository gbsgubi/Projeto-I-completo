// Camada de acesso à API local (mesma origem — nenhuma chamada externa).

async function tratar(resposta) {
  if (!resposta.ok) {
    let detalhe = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      if (corpo.detail) detalhe = corpo.detail;
    } catch { /* corpo não-JSON: mantém o detalhe padrão */ }
    throw new Error(detalhe);
  }
  return resposta.json();
}

export async function verificarArquivo(arquivo) {
  const dados = new FormData();
  dados.append("arquivo", arquivo);
  return tratar(await fetch("/api/verificar", { method: "POST", body: dados }));
}

export async function listarExemplos() {
  return tratar(await fetch("/api/exemplos"));
}

export async function verificarExemplo(numero) {
  return tratar(await fetch(`/api/exemplos/${numero}/verificar`, { method: "POST" }));
}

export function urlMinuta(minutaId) {
  return `/api/minuta/${minutaId}`;
}
