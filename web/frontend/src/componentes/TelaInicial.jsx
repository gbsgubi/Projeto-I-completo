import { useRef, useState } from "react";
import { verificarArquivo } from "../api.js";
import Galeria from "./Galeria.jsx";

function IconeUpload({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
         strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M12 16V4m0 0-4 4m4-4 4 4" />
      <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
    </svg>
  );
}

export default function TelaInicial({ aoDiagnosticar }) {
  const inputRef = useRef(null);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState(null);
  const [arrastando, setArrastando] = useState(false);

  async function enviar(arquivo) {
    if (!arquivo) return;
    setErro(null);
    setOcupado(true);
    try {
      const dados = await verificarArquivo(arquivo);
      aoDiagnosticar(dados, arquivo.name);
    } catch (e) {
      setErro(e.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-10 surgir">
      {/* ---- hero ---- */}
      <div className="text-center mb-8">
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
          Verifique a minuta <span className="text-blue-700">antes</span> de enviá-la
        </h2>
        <p className="mt-2 text-sm sm:text-base text-slate-500 max-w-2xl mx-auto">
          O verificador aplica as regras do Manual de Contestação 2024 e devolve o
          diagnóstico com cada problema grifado no lugar exato do documento.
        </p>
      </div>

      {/* ---- zona de upload ---- */}
      <section
        className={`relative rounded-2xl p-10 text-center bg-white shadow-sm transition-all
          border-2 border-dashed
          ${arrastando
            ? "border-blue-500 bg-blue-50/60 ring-4 ring-blue-100 scale-[1.01]"
            : "border-slate-300 hover:border-slate-400"}`}
        onDragOver={(e) => { e.preventDefault(); setArrastando(true); }}
        onDragLeave={() => setArrastando(false)}
        onDrop={(e) => {
          e.preventDefault();
          setArrastando(false);
          enviar(e.dataTransfer.files?.[0]);
        }}
      >
        <div className={`mx-auto mb-4 grid place-items-center w-16 h-16 rounded-2xl
                         transition-colors
                         ${arrastando ? "bg-blue-100 text-blue-700" : "bg-blue-50 text-blue-600"}`}>
          <IconeUpload className="w-8 h-8" />
        </div>
        <p className="text-lg font-semibold mb-1">
          {arrastando ? "Pode soltar!" : "Verificar uma minuta de contestação"}
        </p>
        <p className="text-sm text-slate-500 mb-5">
          Arraste um arquivo <b>.pdf</b> ou <b>.html</b> até aqui, ou
        </p>
        <button
          className="px-6 py-2.5 rounded-xl bg-blue-700 text-white font-medium
                     shadow-sm shadow-blue-700/30 transition
                     hover:bg-blue-800 hover:shadow-md active:scale-[0.98]
                     disabled:opacity-50 disabled:pointer-events-none"
          disabled={ocupado}
          onClick={() => inputRef.current?.click()}
        >
          {ocupado ? (
            <span className="inline-flex items-center gap-2">
              <span className="w-4 h-4 rounded-full border-2 border-white/40
                               border-t-white animate-spin" aria-hidden />
              Verificando…
            </span>
          ) : "Escolher arquivo"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.html"
          className="hidden"
          onChange={(e) => enviar(e.target.files?.[0])}
        />
        {erro && (
          <p className="mt-5 text-sm text-red-700 bg-red-50 border border-red-200
                        rounded-lg px-4 py-2 inline-block">{erro}</p>
        )}
      </section>

      {/* ---- galeria de exemplos ---- */}
      <Galeria aoDiagnosticar={aoDiagnosticar} />
    </main>
  );
}
