import { CLASSES_BADGE } from "../constantes.js";

function Contador({ rotulo, valor, classe }) {
  return (
    <div className={`rounded px-2 py-1 text-center border ${classe}`}>
      <div className="text-lg font-bold leading-none">{valor}</div>
      <div className="text-[10px] uppercase tracking-wide">{rotulo}</div>
    </div>
  );
}

export default function PainelDiagnostico({
  dados, filtro, aoFiltrar, hoverId, aoHover, aoClicarItem,
}) {
  const reprovado = dados.veredito === "REPROVADO";
  const { resumo } = dados;

  // agrupa pelos blocos do verificador, preservando a ordem de aparição
  const grupos = [];
  const indice = new Map();
  for (const r of dados.resultados) {
    if (filtro === "ERRO" && r.status !== "ERRO") continue;
    if (!indice.has(r.bloco)) {
      indice.set(r.bloco, grupos.length);
      grupos.push({ bloco: r.bloco, itens: [] });
    }
    grupos[indice.get(r.bloco)].itens.push(r);
  }

  return (
    <aside className="flex flex-col gap-3">
      {/* ---- banner de veredito ---- */}
      <div className={`rounded-xl p-4 border-2
        ${reprovado ? "bg-red-50 border-red-400" : "bg-green-50 border-green-400"}`}>
        <p className={`text-2xl font-black text-center
          ${reprovado ? "text-red-700" : "text-green-700"}`}>
          {dados.veredito}
        </p>
        <div className="grid grid-cols-4 gap-2 mt-3 text-slate-700">
          <Contador rotulo="Erro" valor={resumo.erro} classe={CLASSES_BADGE.ERRO} />
          <Contador rotulo="Verificar" valor={resumo.verificar} classe={CLASSES_BADGE.VERIFICAR} />
          <Contador rotulo="OK" valor={resumo.ok} classe={CLASSES_BADGE.OK} />
          <Contador rotulo="Info" valor={resumo.info} classe={CLASSES_BADGE.INFO} />
        </div>
      </div>

      {/* ---- filtro ---- */}
      <div className="flex rounded-lg overflow-hidden border border-slate-300 text-sm">
        {[["TODOS", "Todos os status"], ["ERRO", "Só ERRO"]].map(([valor, rotulo]) => (
          <button
            key={valor}
            onClick={() => aoFiltrar(valor)}
            className={`flex-1 py-1.5 font-medium transition
              ${filtro === valor ? "bg-slate-800 text-white" : "bg-white hover:bg-slate-50"}`}
          >
            {rotulo}
          </button>
        ))}
      </div>

      {/* ---- itens agrupados por bloco ---- */}
      {grupos.length === 0 && (
        <p className="text-sm text-slate-500 bg-white rounded-lg border border-slate-200 p-4">
          Nenhum item com o filtro atual.
        </p>
      )}
      {grupos.map((grupo) => (
        <section key={grupo.bloco} className="bg-white rounded-lg border border-slate-200">
          <h3 className="px-3 py-2 text-xs font-bold uppercase tracking-wide
                         text-slate-500 border-b border-slate-100">
            {grupo.bloco}
          </h3>
          <ul>
            {grupo.itens.map((r) => (
              <li
                key={r.regra_id}
                onMouseEnter={() => r.localizavel && aoHover(r.regra_id)}
                onMouseLeave={() => aoHover(null)}
                onClick={() => r.localizavel && aoClicarItem(r.regra_id)}
                className={`px-3 py-2 border-b border-slate-100 last:border-b-0 text-sm
                  ${r.localizavel ? "cursor-pointer" : ""}
                  ${hoverId === r.regra_id ? "bg-blue-50 ring-1 ring-inset ring-blue-300" : ""}`}
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`px-1.5 py-0.5 rounded border text-[11px] font-bold
                    ${CLASSES_BADGE[r.status]}`}>
                    {r.status}
                  </span>
                  <span className="font-mono text-[11px] text-slate-400">{r.regra_id}</span>
                </div>
                <p className="font-medium mt-1">{r.descricao}</p>
                <p className="text-slate-600">{r.mensagem}</p>
                {r.evidencia && (
                  <p className="mt-1 text-xs italic text-slate-500 line-clamp-2">
                    {r.evidencia}
                  </p>
                )}
                {r.localizavel ? (
                  <p className="mt-1 text-xs text-blue-700">
                    🔍 clique para ver o trecho grifado no documento
                  </p>
                ) : (
                  (r.status === "ERRO" || r.status === "VERIFICAR") && (
                    <p className="mt-1 text-xs text-slate-400">
                      ⚐ sem posição no documento (regra de ausência)
                    </p>
                  )
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </aside>
  );
}
