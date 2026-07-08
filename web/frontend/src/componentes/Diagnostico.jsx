import { useRef, useState } from "react";
import { urlMinuta } from "../api.js";
import VisualizadorPdf from "./VisualizadorPdf.jsx";
import PainelDiagnostico from "./PainelDiagnostico.jsx";

export default function Diagnostico({ dados, titulo, aoVoltar }) {
  const [filtro, setFiltro] = useState("TODOS"); // "TODOS" | "ERRO"
  const [hoverId, setHoverId] = useState(null);
  const [pulsoId, setPulsoId] = useState(null);
  const timeoutPulso = useRef(null);

  const ehPdf = dados.tipo === "pdf";
  const reprovado = dados.veredito === "REPROVADO";

  /** Clique num item localizável do painel: rola até o grifo e o faz pulsar. */
  function irParaGrifo(regraId) {
    const alvo = document.getElementById(`grifo-${regraId}`);
    if (!alvo) return;
    alvo.scrollIntoView({ behavior: "smooth", block: "center" });
    clearTimeout(timeoutPulso.current);
    setPulsoId(regraId);
    timeoutPulso.current = setTimeout(() => setPulsoId(null), 1700);
  }

  return (
    <main className="max-w-[1500px] mx-auto px-4 py-4">
      {/* ---- barra superior ---- */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <button
          onClick={aoVoltar}
          className="px-3 py-1.5 rounded-lg bg-white border border-slate-300
                     text-sm hover:bg-slate-50"
        >
          ← Voltar
        </button>
        <h2 className="font-semibold truncate">{titulo}</h2>
        <span className={`px-3 py-1 rounded-full text-sm font-bold
          ${reprovado ? "bg-red-600 text-white" : "bg-green-600 text-white"}`}>
          {dados.veredito}
        </span>
      </div>

      {/* ---- duas colunas: PDF grifado + painel (empilha no mobile) ---- */}
      <div className={ehPdf ? "grid gap-4 lg:grid-cols-[minmax(0,1fr)_440px]" : ""}>
        {ehPdf ? (
          <VisualizadorPdf
            url={urlMinuta(dados.minuta_id)}
            resultados={dados.resultados}
            filtro={filtro}
            hoverId={hoverId}
            pulsoId={pulsoId}
            aoHover={setHoverId}
          />
        ) : (
          <p className="mb-4 text-sm text-slate-600 bg-amber-50 border border-amber-200
                        rounded-lg px-4 py-3">
            Minuta em HTML: o diagnóstico completo está no painel abaixo. A
            visualização com grifos no documento está disponível apenas para PDF.
          </p>
        )}

        <div className="lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto">
          <PainelDiagnostico
            dados={dados}
            filtro={filtro}
            aoFiltrar={setFiltro}
            hoverId={hoverId}
            aoHover={setHoverId}
            aoClicarItem={irParaGrifo}
          />
        </div>
      </div>
    </main>
  );
}
