import { useEffect, useState } from "react";
import { listarExemplos, verificarExemplo } from "../api.js";

// gabarito usa APROVAR/REPROVAR; o verificador emite APROVADO/REPROVADO
const MAPA_ESPERADO = { APROVAR: "APROVADO", REPROVAR: "REPROVADO" };

function BadgeVeredito({ valor }) {
  if (!valor) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full
                       text-[11px] font-medium bg-slate-100 text-slate-400">
        — ainda não verificado
      </span>
    );
  }
  const aprovado = valor.startsWith("APROVA");
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full
                      text-[11px] font-bold
      ${aprovado ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${aprovado ? "bg-green-500" : "bg-red-500"}`} />
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

  // resumo esperado × obtido das peças já verificadas
  const conferidas = exemplos.filter(
    (ex) => resultados[ex.numero] && MAPA_ESPERADO[ex.esperado]
  );
  const acertos = conferidas.filter(
    (ex) => resultados[ex.numero].veredito === MAPA_ESPERADO[ex.esperado]
  ).length;

  return (
    <section className="mt-12">
      <div className="flex flex-wrap items-end justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-bold tracking-tight flex items-center gap-2">
            Banco de testes
            <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-600
                             text-xs font-semibold">
              {exemplos.length} peças
            </span>
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            {exemplos[0]?.arquivo} … {exemplos.at(-1)?.arquivo} — veredito esperado
            do gabarito × obtido pelo verificador. Clique numa peça para o diagnóstico.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {conferidas.length > 0 && (
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full
              ${acertos === conferidas.length
                ? "bg-green-100 text-green-800"
                : "bg-amber-100 text-amber-800"}`}>
              {acertos}/{conferidas.length} de acordo com o gabarito
            </span>
          )}
          <button
            className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-medium
                       shadow-sm transition hover:bg-slate-700 active:scale-[0.98]
                       disabled:opacity-50 disabled:pointer-events-none"
            disabled={ocupado !== null}
            onClick={verificarTodas}
          >
            {ocupado === "todas" ? (
              <span className="inline-flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded-full border-2 border-white/40
                                 border-t-white animate-spin" aria-hidden />
                Verificando… ({conferidas.length}/{exemplos.length})
              </span>
            ) : "Verificar todas"}
          </button>
        </div>
      </div>

      {erro && (
        <p className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200
                      rounded-lg px-4 py-2">{erro}</p>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {exemplos.map((ex) => {
          const obtido = resultados[ex.numero]?.veredito ?? null;
          const esperado = MAPA_ESPERADO[ex.esperado] ?? null;
          const acerto = obtido && esperado ? obtido === esperado : null;
          const carregando = ocupado === ex.numero;
          return (
            <button
              key={ex.numero}
              onClick={() => abrir(ex)}
              disabled={ocupado !== null}
              className="group text-left bg-white rounded-xl border border-slate-200 p-4
                         shadow-sm transition-all hover:border-blue-400 hover:shadow-md
                         hover:-translate-y-0.5 disabled:opacity-60
                         disabled:pointer-events-none"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="inline-flex items-center gap-2">
                  <span className="grid place-items-center w-8 h-8 rounded-lg
                                   bg-slate-100 text-slate-600 font-mono text-xs
                                   font-bold group-hover:bg-blue-50
                                   group-hover:text-blue-700 transition-colors">
                    {carregando ? (
                      <span className="w-3.5 h-3.5 rounded-full border-2
                                       border-slate-300 border-t-slate-600
                                       animate-spin" aria-hidden />
                    ) : ex.numero}
                  </span>
                  <span className="font-semibold text-slate-800">
                    Contestação {ex.numero}
                  </span>
                </span>
                {acerto !== null && (
                  <span
                    title={acerto ? "veredito bate com o gabarito"
                                  : "veredito diverge do gabarito — possível regressão"}
                    className={`grid place-items-center w-6 h-6 rounded-full text-xs
                                font-bold
                      ${acerto ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}
                  >
                    {acerto ? "✓" : "✕"}
                  </span>
                )}
              </div>
              <div className="text-xs grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 items-center">
                <span className="text-slate-400 font-medium">Esperado</span>
                <span><BadgeVeredito valor={ex.esperado} /></span>
                <span className="text-slate-400 font-medium">Obtido</span>
                <span><BadgeVeredito valor={obtido} /></span>
              </div>
              {ex.motivo && (
                <p className="mt-3 pt-3 border-t border-slate-100 text-xs
                              text-slate-500 line-clamp-2">
                  {ex.motivo}
                </p>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}
