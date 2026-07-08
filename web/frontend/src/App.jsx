import { useEffect, useState } from "react";
import TelaInicial from "./componentes/TelaInicial.jsx";
import Diagnostico from "./componentes/Diagnostico.jsx";
import { verificarExemplo } from "./api.js";

export default function App() {
  // dois "estados de tela": início (upload + galeria) e diagnóstico
  const [diagnostico, setDiagnostico] = useState(null); // { dados, titulo }

  // deep-link de demonstração: ?exemplo=17 abre direto o diagnóstico da peça
  useEffect(() => {
    const numero = new URLSearchParams(window.location.search).get("exemplo");
    if (!numero) return;
    verificarExemplo(numero)
      .then((dados) => setDiagnostico({ dados, titulo: `contestacao_${numero}.pdf` }))
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen text-slate-900">
      <header className="bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800
                         text-white shadow-lg border-b-2 border-blue-700">
        <div className="max-w-[1500px] mx-auto px-6 py-4 flex items-center gap-4">
          <span className="grid place-items-center w-11 h-11 rounded-xl text-2xl
                           bg-blue-600/25 ring-1 ring-blue-400/40 shrink-0">
            ⚖️
          </span>
          <div className="min-w-0">
            <h1 className="font-bold text-lg leading-tight tracking-tight">
              Verificador de Contestação
            </h1>
            <p className="text-xs text-slate-400 leading-tight">
              Camada determinística (Fase 1) · minutas de aposentadoria especial
            </p>
          </div>
          <span className="ml-auto hidden sm:inline-flex items-center gap-1.5 px-3 py-1
                           rounded-full text-xs font-medium bg-white/10 ring-1
                           ring-white/20 text-slate-200 shrink-0">
            <span aria-hidden>🔒</span> 100% local — nenhum dado sai da máquina
          </span>
        </div>
      </header>

      {diagnostico ? (
        <Diagnostico
          dados={diagnostico.dados}
          titulo={diagnostico.titulo}
          aoVoltar={() => setDiagnostico(null)}
        />
      ) : (
        <TelaInicial aoDiagnosticar={(dados, titulo) => setDiagnostico({ dados, titulo })} />
      )}

      <footer className="max-w-[1500px] mx-auto px-6 py-6 text-center text-xs text-slate-400">
        Demonstração — Fase 2 · o veredito e todas as verificações vêm da camada
        determinística; nenhuma regra é reimplementada na interface.
      </footer>
    </div>
  );
}
