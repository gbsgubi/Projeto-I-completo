import { useEffect, useState } from "react";
import { listarExemplos, verificarExemplo } from "../api.js";

// gabarito usa APROVAR/REPROVAR; o verificador emite APROVADO/REPROVADO
const MAPA_ESPERADO = { APROVAR: "APROVADO", REPROVAR: "REPROVADO" };

function BadgeVeredito({ valor }) {
  if (!valor) return <span className="text-slate-400">—</span>;
  const aprovado = valor.startsWith("APROVA");
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-bold
      ${aprovado ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
      {valor}
    </span>
  );
}

export default function Galeria({ aoDiagnosticar }) {
  const [exemplos, setExemplos] = useState([]);
  const [resultados, setResultados] = useState({}); // numero -> dados
  const [ocupado, setOcupado] = useState(null); // numero | "todas" | null
  const [erro, setErro] = useState(null);

  useEffect(() => {
    listarExemplos().then(setExemplos).catch((e) => setErro(e.message));
  }, []);

  async function verificar(numero) {
    if (resultados[numero]) return resultados[numero];
    const dados = await verificarExemplo(numero);
    setResultados((r) => ({ ...r, [numero]: dados }));
    return dados;
  }

  async function abrir(exemplo) {
    setErro(null);
    setOcupado(exemplo.numero);
    try {
      const dados = await verificar(exemplo.numero);
      aoDiagnosticar(dados, exemplo.arquivo);
    } catch (e) {
      setErro(e.message);
    } finally {
      setOcupado(null);
    }
  }

  async function verificarTodas() {
    setErro(null);
    setOcupado("todas");
    try {
      for (const ex of exemplos) await verificar(ex.numero);
    } catch (e) {
      setErro(e.message);
    } finally {
      setOcupado(null);
    }
  }

  if (!exemplos.length) return null;

  return (
    <section className="mt-10">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-lg font-semibold">Exemplos do banco de testes</h2>
          <p className="text-sm text-slate-500">
            {exemplos.length} peças ({exemplos[0]?.arquivo} … {exemplos.at(-1)?.arquivo}) com o
            veredito esperado do gabarito. Clique numa peça para ver o diagnóstico.
          </p>
        </div>
        <button
          className="px-4 py-2 rounded-lg bg-slate-800 text-white text-sm
                     hover:bg-slate-700 disabled:opacity-50 shrink-0"
          disabled={ocupado !== null}
          onClick={verificarTodas}
        >
          {ocupado === "todas" ? "Verificando…" : "Verificar todas"}
        </button>
      </div>

      {erro && (
        <p className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200
                      rounded px-3 py-2">{erro}</p>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {exemplos.map((ex) => {
          const obtido = resultados[ex.numero]?.veredito ?? null;
          const esperado = MAPA_ESPERADO[ex.esperado] ?? null;
          const acerto = obtido && esperado ? obtido === esperado : null;
          return (
            <button
              key={ex.numero}
              onClick={() => abrir(ex)}
              disabled={ocupado !== null}
              className="text-left bg-white rounded-lg border border-slate-200 p-4
                         hover:border-blue-400 hover:shadow transition disabled:opacity-60"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono font-bold text-slate-700">
                  {ocupado === ex.numero ? "⏳ " : ""}Contestação {ex.numero}
                </span>
                {acerto !== null && (
                  <span title={acerto ? "veredito bate com o gabarito"
                                      : "veredito diverge do gabarito (checagem da fase LLM)"}
                        className={acerto ? "text-green-600" : "text-red-600"}>
                    {acerto ? "✔" : "✘"}
                  </span>
                )}
              </div>
              <div className="text-xs grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 items-center">
                <span className="text-slate-500">Esperado:</span>
                <span><BadgeVeredito valor={ex.esperado} /></span>
                <span className="text-slate-500">Obtido:</span>
                <span><BadgeVeredito valor={obtido} /></span>
              </div>
              {ex.motivo && (
                <p className="mt-2 text-xs text-slate-500 line-clamp-2">{ex.motivo}</p>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}
