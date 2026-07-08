import {
  ACENTO_ITEM, CLASSES_BADGE, GLIFO_STATUS, PONTO_STATUS,
} from "../constantes.js";

/* Stat tile: rótulo + ponto de status em cima, valor em tinta neutra embaixo.
   A identidade do status vem do ponto colorido + rótulo, nunca da cor sozinha. */
function Contador({ rotulo, valor, status }) {
  const vazio = valor === 0;
  return (
    <div className={`rounded-xl px-2 py-2 text-center bg-white border border-slate-200
                     shadow-sm ${vazio ? "opacity-55" : ""}`}>
      <div className="flex items-center justify-center gap-1.5 mb-1">
        <span className={`w-2 h-2 rounded-full ${PONTO_STATUS[status]}`} aria-hidden />
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          {rotulo}
        </span>
      </div>
      <div className="text-2xl font-bold leading-none text-slate-900">{valor}</div>
    </div>
  );
}

function BadgeStatus({ status }) {
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md border
                      text-[11px] font-bold ${CLASSES_BADGE[status]}`}>
      <span aria-hidden>{GLIFO_STATUS[status]}</span>
      {status}
    </span>
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
      <div className={`rounded-2xl p-4 border shadow-sm
        ${reprovado
          ? "bg-gradient-to-br from-red-50 to-red-100/60 border-red-200"
          : "bg-gradient-to-br from-green-50 to-green-100/60 border-green-200"}`}>
        <div className="flex items-center justify-center gap-3">
          <span className={`grid place-items-center w-10 h-10 rounded-full text-xl
                            font-black text-white shadow-sm
            ${reprovado ? "bg-red-600" : "bg-green-600"}`} aria-hidden>
            {reprovado ? "✕" : "✓"}
          </span>
          <div>
            <p className={`text-2xl font-black leading-none tracking-tight
              ${reprovado ? "text-red-700" : "text-green-700"}`}>
              {dados.veredito}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {reprovado
                ? `${resumo.erro} erro${resumo.erro === 1 ? "" : "s"} — corrigir antes de enviar ao procurador`
                : "nenhum erro determinístico encontrado"}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-2 mt-4">
          <Contador rotulo="Erro" valor={resumo.erro} status="ERRO" />
          <Contador rotulo="Verificar" valor={resumo.verificar} status="VERIFICAR" />
          <Contador rotulo="OK" valor={resumo.ok} status="OK" />
          <Contador rotulo="Info" valor={resumo.info} status="INFO" />
        </div>
      </div>

      {/* ---- filtro segmentado ---- */}
      <div className="flex rounded-xl bg-slate-200/80 p-1 text-sm gap-1">
        {[["TODOS", "Todos os status"], ["ERRO", `Só ERRO (${resumo.erro})`]].map(
          ([valor, rotulo]) => (
            <button
              key={valor}
              onClick={() => aoFiltrar(valor)}
              className={`flex-1 py-1.5 rounded-lg font-medium transition
                ${filtro === valor
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"}`}
            >
              {rotulo}
            </button>
          )
        )}
      </div>

      {/* ---- itens agrupados por bloco ---- */}
      {grupos.length === 0 && (
        <p className="text-sm text-slate-500 bg-white rounded-xl border
                      border-slate-200 p-4 text-center">
          Nenhum item com o filtro atual.
        </p>
      )}
      {grupos.map((grupo) => (
        <section key={grupo.bloco}
                 className="bg-white rounded-xl border border-slate-200 shadow-sm
                            overflow-hidden">
          <h3 className="px-3 py-2 text-xs font-bold uppercase tracking-wider
                         text-slate-500 bg-slate-50 border-b border-slate-200
                         flex items-center justify-between">
            {grupo.bloco}
            <span className="font-mono font-semibold text-slate-400 normal-case">
              {grupo.itens.length}
            </span>
          </h3>
          <ul>
            {grupo.itens.map((r) => (
              <li
                key={r.regra_id}
                onMouseEnter={() => r.localizavel && aoHover(r.regra_id)}
                onMouseLeave={() => aoHover(null)}
                onClick={() => r.localizavel && aoClicarItem(r.regra_id)}
                className={`px-3 py-2.5 border-b border-slate-100 last:border-b-0
                  text-sm border-l-[3px] transition-colors
                  ${ACENTO_ITEM[r.status] ?? "border-l-slate-200"}
                  ${r.localizavel ? "cursor-pointer hover:bg-slate-50" : ""}
                  ${hoverId === r.regra_id ? "bg-blue-50 ring-1 ring-inset ring-blue-300" : ""}`}
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <BadgeStatus status={r.status} />
                  <span className="font-mono text-[11px] text-slate-400">{r.regra_id}</span>
                </div>
                <p className="font-medium mt-1.5 leading-snug">{r.descricao}</p>
                <p className="text-slate-600 mt-0.5 leading-snug">{r.mensagem}</p>
                {r.evidencia && (
                  <p className="mt-1.5 text-xs italic text-slate-500 line-clamp-2
                                bg-slate-50 border border-slate-100 rounded-md
                                px-2 py-1">
                    {r.evidencia}
                  </p>
                )}
                {r.localizavel ? (
                  <p className="mt-1.5 text-xs font-medium text-blue-700
                                inline-flex items-center gap-1">
                    <span aria-hidden>🔍</span> clique para ver o trecho grifado
                  </p>
                ) : (
                  (r.status === "ERRO" || r.status === "VERIFICAR") && (
                    <p className="mt-1.5 text-xs text-slate-400
                                  inline-flex items-center gap-1">
                      <span aria-hidden>⚐</span> sem posição no documento (regra de ausência)
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
