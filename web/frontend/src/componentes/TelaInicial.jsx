import { useRef, useState } from "react";
import { verificarArquivo } from "../api.js";
import Galeria from "./Galeria.jsx";

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
    <main className="max-w-5xl mx-auto px-6 py-8">
      {/* ---- zona de upload ---- */}
      <section
        className={`border-2 border-dashed rounded-xl p-10 text-center bg-white transition
          ${arrastando ? "border-blue-500 bg-blue-50" : "border-slate-300"}`}
        onDragOver={(e) => { e.preventDefault(); setArrastando(true); }}
        onDragLeave={() => setArrastando(false)}
        onDrop={(e) => {
          e.preventDefault();
          setArrastando(false);
          enviar(e.dataTransfer.files?.[0]);
        }}
      >
        <p className="text-lg font-semibold mb-1">Verificar uma minuta de contestação</p>
        <p className="text-sm text-slate-500 mb-4">
          Arraste um arquivo <b>.pdf</b> ou <b>.html</b> aqui, ou
        </p>
        <button
          className="px-5 py-2 rounded-lg bg-blue-700 text-white font-medium
                     hover:bg-blue-800 disabled:opacity-50"
          disabled={ocupado}
          onClick={() => inputRef.current?.click()}
        >
          {ocupado ? "Verificando…" : "Escolher arquivo"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.html"
          className="hidden"
          onChange={(e) => enviar(e.target.files?.[0])}
        />
        {erro && (
          <p className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200
                        rounded px-3 py-2 inline-block">{erro}</p>
        )}
      </section>

      {/* ---- galeria de exemplos ---- */}
      <Galeria aoDiagnosticar={aoDiagnosticar} />
    </main>
  );
}
