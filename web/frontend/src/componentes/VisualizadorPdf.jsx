import { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
// worker empacotado pelo Vite — nenhum CDN
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { CORES_GRIFO, BORDAS_GRIFO } from "../constantes.js";

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;

/** Uma página do PDF: canvas + overlays de grifo posicionados em %. */
function Pagina({ pagina, numero, grifos, hoverId, pulsoId, aoHover }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    // renderiza uma única vez em resolução alta; o CSS escala para 100% da
    // coluna — como os grifos usam %, nunca há descasamento de coordenadas.
    const escala = 1.5 * Math.min(window.devicePixelRatio || 1, 2);
    const viewport = pagina.getViewport({ scale: escala });
    const canvas = canvasRef.current;
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    const tarefa = pagina.render({ canvasContext: canvas.getContext("2d"), viewport });
    return () => tarefa.cancel();
  }, [pagina]);

  return (
    <div className="relative shadow-md border border-slate-300 bg-white">
      <canvas ref={canvasRef} className="block w-full h-auto" />

      {grifos.map(({ resultado, destaque, ehPrimeiro }, i) => {
        const [x0, y0, x1, y1] = destaque.rect;
        const status = resultado.status;
        const emHover = hoverId === resultado.regra_id;
        return (
          <div
            key={`${resultado.regra_id}-${i}`}
            id={ehPrimeiro ? `grifo-${resultado.regra_id}` : undefined}
            title={`[${status}] ${resultado.descricao}`}
            onMouseEnter={() => aoHover(resultado.regra_id)}
            onMouseLeave={() => aoHover(null)}
            className={`absolute rounded-[2px] cursor-help
              ${pulsoId === resultado.regra_id ? "grifo-pulsando" : ""}`}
            style={{
              left: `${x0 * 100}%`,
              top: `${y0 * 100}%`,
              width: `${(x1 - x0) * 100}%`,
              height: `${(y1 - y0) * 100}%`,
              backgroundColor: CORES_GRIFO[status] ?? CORES_GRIFO.INFO,
              border: `1.5px solid ${emHover ? (BORDAS_GRIFO[status] ?? BORDAS_GRIFO.INFO) : "transparent"}`,
            }}
          >
            {ehPrimeiro && (
              <span
                className="absolute -top-4 left-0 px-1 rounded-sm text-[9px]
                           font-mono font-bold text-white whitespace-nowrap"
                style={{ backgroundColor: BORDAS_GRIFO[status] ?? BORDAS_GRIFO.INFO }}
              >
                {resultado.regra_id}
              </span>
            )}
          </div>
        );
      })}

      <span className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded
                       bg-slate-900/60 text-white text-[10px] font-medium">
        página {numero}
      </span>
    </div>
  );
}

export default function VisualizadorPdf({ url, resultados, filtro, hoverId, pulsoId, aoHover }) {
  const [paginas, setPaginas] = useState([]);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    let cancelado = false;
    const tarefa = pdfjsLib.getDocument(url);
    (async () => {
      try {
        const doc = await tarefa.promise;
        const carregadas = [];
        for (let n = 1; n <= doc.numPages; n++) carregadas.push(await doc.getPage(n));
        if (!cancelado) setPaginas(carregadas);
      } catch (e) {
        if (!cancelado) setErro(`Falha ao carregar o PDF: ${e.message}`);
      }
    })();
    return () => { cancelado = true; tarefa.destroy(); };
  }, [url]);

  // grifos visíveis segundo o filtro, agrupados por página
  const visiveis = resultados.filter(
    (r) => r.localizavel && (filtro === "TODOS" || r.status === "ERRO")
  );
  const porPagina = new Map();
  for (const r of visiveis) {
    r.destaques.forEach((d, idx) => {
      if (!porPagina.has(d.pagina)) porPagina.set(d.pagina, []);
      porPagina.get(d.pagina).push({ resultado: r, destaque: d, ehPrimeiro: idx === 0 });
    });
  }

  if (erro) {
    return <p className="text-sm text-red-700 bg-red-50 border border-red-200
                         rounded-lg px-4 py-3 h-fit">{erro}</p>;
  }

  return (
    <div className="flex flex-col gap-4 min-w-0">
      {paginas.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-10
                        flex flex-col items-center gap-3">
          <span className="w-8 h-8 rounded-full border-[3px] border-slate-200
                           border-t-blue-600 animate-spin" aria-hidden />
          <p className="text-sm text-slate-500">Carregando o documento…</p>
        </div>
      )}
      {paginas.map((pagina, i) => (
        <Pagina
          key={i}
          pagina={pagina}
          numero={i + 1}
          grifos={porPagina.get(i + 1) ?? []}
          hoverId={hoverId}
          pulsoId={pulsoId}
          aoHover={aoHover}
        />
      ))}
    </div>
  );
}
