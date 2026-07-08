import { useState } from "react";
import TelaInicial from "./componentes/TelaInicial.jsx";
import Diagnostico from "./componentes/Diagnostico.jsx";

export default function App() {
  // dois "estados de tela": início (upload + galeria) e diagnóstico
  const [diagnostico, setDiagnostico] = useState(null); // { dados, titulo }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="bg-slate-900 text-white px-6 py-3 flex items-center gap-3 shadow">
        <span className="text-xl">⚖️</span>
        <div>
          <h1 className="font-bold leading-tight">Verificador de Contestação</h1>
          <p className="text-xs text-slate-300 leading-tight">
            Demonstração — Fase 2 · roda 100% local, nenhum dado sai da máquina
          </p>
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
    </div>
  );
}
