import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiSend } from "../api";

type Linha = {
  candidatoId: string;
  linhaOrigem: number;
  nomeExibicao: string | null;
  ultimoCargo: string | null;
  idade: string | null;
  escolaridade: string | null;
  decisao: {
    resultado: string;
    motivos: Array<{
      criterio: string;
      codigo: string;
      valorLido: string | null;
      valorComparado: string | null;
      mensagem: string;
    }>;
    criteriosInativos: string[];
  } | null;
};

function comparado(texto: string) {
  return texto
    .trim()
    .replace(/\s+/g, " ")
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
}

export default function Triagem() {
  const { projetoId } = useParams();
  const [linhas, setLinhas] = useState<Linha[]>([]);
  const [filtro, setFiltro] = useState("todos");
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");

  function carregar() {
    apiGet<{ linhas: Linha[] }>(`/api/projetos/${projetoId}/triagem`)
      .then((r) => setLinhas(r.linhas))
      .catch((e) => setErro(e.message));
  }

  useEffect(() => {
    carregar();
  }, [projetoId]);

  async function executar() {
    setErro("");
    setOk("");
    try {
      const r = await apiSend<{ quantidade: number }>(`/api/projetos/${projetoId}/triagem/executar`, "POST", {});
      setOk(`Triagem executada: ${r.quantidade} candidato(s). Nenhuma chamada de LLM.`);
      carregar();
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  async function exportar() {
    setErro("");
    setOk("");
    try {
      const res = await fetch(`/api/projetos/${projetoId}/triagem/exportar`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = (data as { detail?: string }).detail;
        throw new Error(detail || "Não foi possível exportar a triagem.");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "triagem.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  const visiveis = linhas.filter((l) => {
    if (filtro === "todos") return true;
    if (!l.decisao) return false;
    return l.decisao.resultado === filtro;
  });

  return (
    <>
      <h2>Triagem determinística</h2>
      <p className="lead">Sem LLM. Inelegível mostra todos os motivos, o valor lido e o comparado.</p>
      {erro && <p className="err">{erro}</p>}
      {ok && <p className="ok">{ok}</p>}
      <div className="row" style={{ marginBottom: 12 }}>
        <button className="btn" type="button" onClick={executar}>
          Executar triagem
        </button>
        <button className="btn sec" type="button" onClick={exportar}>
          Exportar Excel
        </button>
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)}>
          <option value="todos">Todos</option>
          <option value="elegivel">Elegível na triagem</option>
          <option value="inelegivel">Inelegível</option>
        </select>
      </div>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Rótulo</th>
              <th>Decisão</th>
              <th>Motivos</th>
              <th>Lido → comparado</th>
              <th>Não aplicado</th>
            </tr>
          </thead>
          <tbody>
            {visiveis.map((l) => (
              <tr key={l.candidatoId}>
                <td>
                  {l.nomeExibicao || l.candidatoId}
                  <div className="muted">linha {l.linhaOrigem}</div>
                </td>
                <td>
                  {!l.decisao ? (
                    "—"
                  ) : l.decisao.resultado === "elegivel" ? (
                    <span className="tag ok">Elegível na triagem</span>
                  ) : (
                    <span className="tag bad">Inelegível</span>
                  )}
                </td>
                <td>
                  {!l.decisao || l.decisao.motivos.length === 0
                    ? "—"
                    : l.decisao.motivos.map((m) => <div key={m.codigo + m.criterio}>{m.mensagem}</div>)}
                </td>
                <td>
                  {l.ultimoCargo != null && (
                    <div>
                      cargo: {l.ultimoCargo} → {comparado(l.ultimoCargo)}
                    </div>
                  )}
                  {l.escolaridade != null && (
                    <div>
                      escolaridade: {l.escolaridade} → {comparado(l.escolaridade)}
                    </div>
                  )}
                  {l.idade != null && <div>idade lida: {l.idade}</div>}
                </td>
                <td>
                  {(l.decisao?.criteriosInativos || []).map((n) => (
                    <div key={n}>
                      {n}: <span className="tag">Não aplicado</span>
                    </div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
