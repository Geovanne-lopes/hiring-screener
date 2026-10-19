import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiGet } from "../api";
import type { Envelope } from "../types";

const ROTULO_SEM_INFORMACAO = "sem informação para julgar esta pergunta";

function schemaNovo(e: Envelope) {
  return Array.isArray(e.avaliacao?.porPergunta);
}

function rotuloPergunta(resultado: string, rotulo?: string) {
  if (resultado === "sem_informacao") return rotulo || ROTULO_SEM_INFORMACAO;
  return rotulo || resultado;
}

function rotuloEstado(e: Envelope) {
  switch (e.resultadoExibicao) {
    case "inelegivel":
      return "Inelegível";
    case "aguardando_resposta":
      return "Aguardando resposta";
    case "elegivel_pendente_ia":
      return "Elegível na triagem — avaliação por IA não executada";
    case "avaliado":
      if (schemaNovo(e)) return "Avaliado";
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

type Ordem = "final" | "tecnica" | "comportamental";

function exibirNota(valor: number | null | undefined) {
  if (valor === null || valor === undefined) return "—";
  return String(valor);
}

function posicaoTexto(posicao: number | null | undefined, total: number | undefined) {
  if (posicao == null || !total) return "—";
  return `${posicao} de ${total}`;
}

function posicaoDaOrdem(e: Envelope, ordem: Ordem) {
  const ranking = e.ranking;
  if (!ranking) return null;
  if (ordem === "tecnica") return ranking.posicaoTecnica;
  if (ordem === "comportamental") return ranking.posicaoComportamental;
  return ranking.posicaoFinal;
}

function classe(e: Envelope) {
  if (e.resultadoExibicao === "inelegivel") return "bad";
  if (e.resultadoExibicao === "aguardando_resposta") return "wait";
  if (e.resultadoExibicao === "falha_avaliacao") return "fail";
  if (schemaNovo(e)) return "";
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
  const [ordem, setOrdem] = useState<Ordem>("final");
  const [soComNota, setSoComNota] = useState(false);
  const [erro, setErro] = useState("");
  const [aberto, setAberto] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ linhas: Envelope[] }>(`/api/projetos/${projetoId}/resultado`)
      .then((r) => setLinhas(r.linhas))
      .catch((e) => setErro(e.message));
  }, [projetoId]);

  async function exportar() {
    setErro("");
    try {
      const filtroNota = soComNota ? "?soComNota=true" : "";
      const res = await fetch(`/api/projetos/${projetoId}/resultado/exportar${filtroNota}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = (data as { detail?: string }).detail;
        throw new Error(detail || "Não foi possível exportar o resultado.");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "resultado.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  const visiveis = linhas
    .filter((l) => {
      if (soComNota && l.ranking?.posicaoFinal == null) return false;
      if (filtro === "todos") return true;
      if (filtro === "pendente") return l.resultadoExibicao === "elegivel_pendente_ia";
      if (filtro === "falha") return l.resultadoExibicao === "falha_avaliacao";
      if (filtro === "aguardando") return l.resultadoExibicao === "aguardando_resposta";
      if (filtro === "inelegivel") return l.resultadoExibicao === "inelegivel";
      if (filtro === "avaliado") return l.resultadoExibicao === "avaliado";
      return true;
    })
    .sort((a, b) => {
      const pa = posicaoDaOrdem(a, ordem);
      const pb = posicaoDaOrdem(b, ordem);
      if (pa == null && pb == null) return a.linhaOrigem - b.linhaOrigem;
      if (pa == null) return 1;
      if (pb == null) return -1;
      if (pa !== pb) return pa - pb;
      return a.linhaOrigem - b.linhaOrigem;
    });

  return (
    <>
      <h2>Resultado</h2>
      <p className="lead">
        Notas e posições do lote. Quem não tem as duas notas fica sem ranking. O julgamento de cada pergunta continua abaixo.
      </p>
      {erro && <p className="err">{erro}</p>}
      <div className="row toolbar" style={{ marginBottom: 12 }}>
        <button className="btn sec" type="button" onClick={exportar}>
          Exportar resultado
        </button>
        <select value={ordem} onChange={(e) => setOrdem(e.target.value as Ordem)} aria-label="Ordenar ranking">
          <option value="final">Ranking final</option>
          <option value="tecnica">Ranking técnico</option>
          <option value="comportamental">Ranking comportamental</option>
        </select>
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)} aria-label="Filtrar estado">
          <option value="todos">Todos</option>
          <option value="inelegivel">Inelegível</option>
          <option value="aguardando">Aguardando</option>
          <option value="pendente">Pendente IA</option>
          <option value="avaliado">Avaliado</option>
          <option value="falha">Falha</option>
        </select>
        <label className="switch inline">
          <input type="checkbox" checked={soComNota} onChange={(e) => setSoComNota(e.target.checked)} />
          Só quem tem nota
        </label>
      </div>
      {visiveis.map((l) => (
        <div className="card" key={l.candidatoId}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <strong>{l.nomeExibicao || l.candidatoId}</strong>
            <span className={`tag ${classe(l)}`}>{rotuloEstado(l)}</span>
          </div>
          <p className="muted">linha {l.linhaOrigem}</p>
          <p>
            Nota técnica {exibirNota(schemaNovo(l) ? l.avaliacao?.notaTecnica : null)} · Ranking técnico{" "}
            {posicaoTexto(l.ranking?.posicaoTecnica, l.ranking?.totalComNota)}
          </p>
          {schemaNovo(l) && l.avaliacao?.justificativaNotaTecnica ? (
            <>
              <p>
                <strong>Justificativa da nota técnica</strong>
              </p>
              <p>{l.avaliacao.justificativaNotaTecnica}</p>
            </>
          ) : null}
          <p>
            Nota comportamental {exibirNota(schemaNovo(l) ? l.avaliacao?.notaComportamental : null)} · Ranking
            comportamental {posicaoTexto(l.ranking?.posicaoComportamental, l.ranking?.totalComNota)}
          </p>
          {schemaNovo(l) && l.avaliacao?.justificativaNotaComportamental ? (
            <>
              <p>
                <strong>Justificativa da nota comportamental</strong>
              </p>
              <p>{l.avaliacao.justificativaNotaComportamental}</p>
            </>
          ) : null}
          <p>
            Nota final {exibirNota(l.ranking?.notaFinal)} · Ranking final{" "}
            {posicaoTexto(l.ranking?.posicaoFinal, l.ranking?.totalComNota)}
          </p>
          {l.ranking?.notaTecnicaZeradaPorFaltaDeInformacao ? (
            <p className="warn">A nota técnica foi zerada por falta de informação para o cruzamento.</p>
          ) : null}
          {l.resultadoExibicao === "inelegivel" &&
            (l.decisao?.motivos || []).map((m) => <p key={m.mensagem}>{m.mensagem}</p>)}
          {l.resultadoExibicao === "avaliado" && l.avaliacao && schemaNovo(l) && (
            <>
              <p>
                <strong>Resumo</strong>
              </p>
              <p>{l.avaliacao.perfil}</p>
              {(l.avaliacao.porPergunta || []).map((p) => (
                <div key={p.perguntaId} style={{ marginTop: 8 }}>
                  <strong>{p.pergunta}</strong>
                  <p>{rotuloPergunta(p.resultado, p.rotulo)}</p>
                  <p>Justificativa da pergunta</p>
                  <p>{p.justificativa}</p>
                  {p.trecho ? <p className="muted">Trecho: {p.trecho}</p> : null}
                </div>
              ))}
              <p className="muted">
                Prompt {l.avaliacao.promptVersionId}
                {l.avaliacao.jobDescriptionVersaoId ? ` · job description ${l.avaliacao.jobDescriptionVersaoId}` : ""}
                {l.avaliacao.criadoEm ? ` · ${l.avaliacao.criadoEm}` : ""}
                {l.avaliacao.usoToken?.total != null
                  ? ` · tokens ${l.avaliacao.usoToken.entrada}/${l.avaliacao.usoToken.saida}/${l.avaliacao.usoToken.total}`
                  : ""}
              </p>
            </>
          )}
          {l.resultadoExibicao === "avaliado" && l.avaliacao && !schemaNovo(l) && (
            <>
              <p>{l.avaliacao.perfil}</p>
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
