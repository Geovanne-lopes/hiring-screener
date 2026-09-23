import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiGet } from "../api";
import type { Envelope } from "../types";

function rotuloEstado(e: Envelope) {
  switch (e.resultadoExibicao) {
    case "inelegivel":
      return "Inelegível";
    case "aguardando_resposta":
      return "Aguardando resposta";
    case "elegivel_pendente_ia":
      return "Elegível na triagem — avaliação por IA não executada";
    case "avaliado":
      return e.avaliacao?.compatibilidade === "compativel"
        ? "Compatível"
        : e.avaliacao?.compatibilidade === "parcial"
          ? "Parcial"
          : e.avaliacao?.compatibilidade === "incompativel"
            ? "Incompatível"
            : "Avaliado";
    case "falha_avaliacao":
      return "Falha de avaliação";
    default:
      return e.resultadoExibicao;
  }
}

function classe(e: Envelope) {
  if (e.resultadoExibicao === "inelegivel") return "bad";
  if (e.resultadoExibicao === "aguardando_resposta") return "wait";
  if (e.resultadoExibicao === "falha_avaliacao") return "fail";
  if (e.avaliacao?.compatibilidade === "compativel") return "ok";
  if (e.avaliacao?.compatibilidade === "parcial") return "mid";
  if (e.avaliacao?.compatibilidade === "incompativel") return "bad";
  return "";
}

export default function Resultado() {
  const { projetoId } = useParams();
  const nav = useNavigate();
  const [linhas, setLinhas] = useState<Envelope[]>([]);
  const [filtro, setFiltro] = useState("todos");
  const [erro, setErro] = useState("");
  const [aberto, setAberto] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ linhas: Envelope[] }>(`/api/projetos/${projetoId}/resultado`)
      .then((r) => setLinhas(r.linhas))
      .catch((e) => setErro(e.message));
  }, [projetoId]);

  const visiveis = linhas.filter((l) => {
    if (filtro === "todos") return true;
    if (filtro === "compativel") return l.avaliacao?.compatibilidade === "compativel";
    if (filtro === "parcial") return l.avaliacao?.compatibilidade === "parcial";
    if (filtro === "incompativel") return l.avaliacao?.compatibilidade === "incompativel";
    if (filtro === "pendente") return l.resultadoExibicao === "elegivel_pendente_ia";
    if (filtro === "falha") return l.resultadoExibicao === "falha_avaliacao";
    if (filtro === "aguardando") return l.resultadoExibicao === "aguardando_resposta";
    if (filtro === "inelegivel") return l.resultadoExibicao === "inelegivel";
    if (filtro === "avaliado") return l.resultadoExibicao === "avaliado";
    return true;
  });

  return (
    <>
      <h2>Resultado</h2>
      <p className="lead">Por candidato: inelegibilidade com motivos, aguardando, ou perfil e compatibilidade.</p>
      {erro && <p className="err">{erro}</p>}
      <select value={filtro} onChange={(e) => setFiltro(e.target.value)} style={{ marginBottom: 12 }}>
        <option value="todos">Todos</option>
        <option value="inelegivel">Inelegível</option>
        <option value="aguardando">Aguardando</option>
        <option value="pendente">Pendente IA</option>
        <option value="avaliado">Avaliado</option>
        <option value="falha">Falha</option>
        <option value="compativel">Compatível</option>
        <option value="parcial">Parcial</option>
        <option value="incompativel">Incompatível</option>
      </select>
      {visiveis.map((l) => (
        <div className="card" key={l.candidatoId}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <strong>{l.nomeExibicao || l.candidatoId}</strong>
            <span className={`tag ${classe(l)}`}>{rotuloEstado(l)}</span>
          </div>
          <p className="muted">linha {l.linhaOrigem}</p>
          {l.resultadoExibicao === "inelegivel" &&
            (l.decisao?.motivos || []).map((m) => <p key={m.mensagem}>{m.mensagem}</p>)}
          {l.resultadoExibicao === "avaliado" && l.avaliacao && (
            <>
              <p>{l.avaliacao.perfil}</p>
              <p>
                Compatibilidade:{" "}
                {l.avaliacao.compatibilidade === "compativel"
                  ? "compatível"
                  : l.avaliacao.compatibilidade === "incompativel"
                    ? "incompatível"
                    : l.avaliacao.compatibilidade}
              </p>
              <button className="btn sec" type="button" onClick={() => setAberto(aberto === l.candidatoId ? null : l.candidatoId)}>
                {aberto === l.candidatoId ? "Ocultar critérios" : "Ver critérios, trechos e versão"}
              </button>
              {aberto === l.candidatoId && (
                <>
                  {(l.avaliacao.justificativasPorCriterio || []).map((j) => (
                    <div key={j.criterioId} style={{ marginTop: 8 }}>
                      <strong>{j.nome}</strong> —{" "}
                      {j.resultado === "sem_informacao" ? "Sem informação nas respostas" : j.resultado}
                      <p>{j.justificativa}</p>
                      {j.trecho ? <p className="muted">Trecho: {j.trecho}</p> : null}
                    </div>
                  ))}
                  <p className="muted">
                    Prompt {l.avaliacao.promptVersionId}
                    {l.avaliacao.criadoEm ? ` · ${l.avaliacao.criadoEm}` : ""}
                    {l.avaliacao.usoToken?.total != null
                      ? ` · tokens ${l.avaliacao.usoToken.entrada}/${l.avaliacao.usoToken.saida}/${l.avaliacao.usoToken.total}`
                      : ""}
                  </p>
                </>
              )}
            </>
          )}
          {l.resultadoExibicao === "falha_avaliacao" && (
            <>
              <p className="err">
                {l.avaliacao?.erro?.codigo}: {l.avaliacao?.erro?.mensagem}
              </p>
              <button
                className="btn"
                type="button"
                onClick={() => nav(`/projetos/${projetoId}/avaliacao?candidato=${encodeURIComponent(l.candidatoId)}`)}
              >
                Avaliar de novo
              </button>
            </>
          )}
        </div>
      ))}
    </>
  );
}
