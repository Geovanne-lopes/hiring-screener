import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { apiGet, apiSend } from "../api";
import type { Envelope } from "../types";

type Lote = {
  linhas: Envelope[];
  faltas: string[];
  llm: { configurada: boolean; modelo: string; baseUrlDefinida: boolean };
};

export default function Avaliacao() {
  const { projetoId } = useParams();
  const [params] = useSearchParams();
  const [lote, setLote] = useState<Lote | null>(null);
  const [sel, setSel] = useState<Record<string, boolean>>({});
  const [confirmar, setConfirmar] = useState(false);
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [tokens, setTokens] = useState<{ entrada: number; saida: number; total: number; registrosSemUso: number } | null>(
    null,
  );

  function carregar() {
    apiGet<Lote>(`/api/projetos/${projetoId}/avaliacao-ia/lote`)
      .then((r) => {
        setLote(r);
        const init: Record<string, boolean> = {};
        const focar = params.get("candidato");
        r.linhas.forEach((l) => {
          init[l.candidatoId] = focar ? l.candidatoId === focar : Boolean(l.incluidoPadrao);
        });
        setSel(init);
      })
      .catch((e) => setErro(e.message));
  }

  useEffect(() => {
    carregar();
  }, [projetoId]);

  const selecionados = useMemo(
    () => (lote?.linhas || []).filter((l) => l.selecionavel && sel[l.candidatoId]).map((l) => l.candidatoId),
    [lote, sel],
  );

  async function enviar() {
    setErro("");
    setOk("");
    setEnviando(true);
    try {
      const r = await apiSend<{
        enviados: string[];
        resultados: Array<{ candidatoId: string; estado: string; erro?: { mensagem?: string } | null }>;
        tokens: { entrada: number; saida: number; total: number; registrosSemUso: number };
      }>(`/api/projetos/${projetoId}/avaliacao-ia/executar`, "POST", {
        candidatoIds: selecionados,
        confirmar: true,
      });
      const falhas = r.resultados.filter((item) => item.estado !== "sucesso");
      const mensagemFalha = falhas.map((item) => item.erro?.mensagem).find(Boolean);
      if (falhas.length === r.resultados.length && mensagemFalha) {
        setErro(mensagemFalha);
        return;
      }
      setConfirmar(false);
      setTokens(r.tokens);
      if (falhas.length > 0 && mensagemFalha) {
        setErro(`${mensagemFalha} ${r.resultados.length - falhas.length} avaliação(ões) concluída(s).`);
      } else {
        setOk(`Avaliação concluída. Enviados: ${r.enviados.length}.`);
      }
      carregar();
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  if (!lote) {
    return (
      <>
        <h2>Avaliação por IA</h2>
        {erro ? <p className="err">{erro}</p> : <p>Carregando…</p>}
      </>
    );
  }

  const grupos = {
    elegiveis: lote.linhas.filter((l) => l.selecionavel),
    aguardando: lote.linhas.filter((l) => l.resultadoExibicao === "aguardando_resposta"),
    inelegiveis: lote.linhas.filter((l) => l.resultadoExibicao === "inelegivel"),
  };
  const pode = selecionados.length > 0 && lote.faltas.length === 0;

  return (
    <>
      <h2>Avaliação por IA das respostas</h2>
      <p className="lead">Só elegíveis com resposta utilizável. Inelegível não gera chamada.</p>
      {erro && <p className="err">{erro}</p>}
      {ok && <p className="ok">{ok}</p>}
      {lote.llm.modelo && <p className="muted">Modelo: {lote.llm.modelo}</p>}
      {lote.faltas.map((f) => (
        <p className="warn" key={f}>
          {f}
        </p>
      ))}
      {tokens && (
        <p>
          Tokens desta execução: entrada {tokens.entrada}, saída {tokens.saida}, total {tokens.total}
          {tokens.registrosSemUso > 0 ? ` · ${tokens.registrosSemUso} registro(s) sem uso reportado` : ""}
        </p>
      )}

      <div className="card">
        <h3>Elegíveis com resposta utilizável</h3>
        {grupos.elegiveis.map((l) => (
          <label key={l.candidatoId} className="switch">
            <input
              type="checkbox"
              checked={Boolean(sel[l.candidatoId])}
              onChange={(e) => setSel({ ...sel, [l.candidatoId]: e.target.checked })}
            />
            Incluir nesta avaliação — {l.nomeExibicao || l.candidatoId}
            {l.resultadoExibicao === "avaliado" && (
              <span className="muted"> (já avaliado: novo disparo gera nova avaliação e não reescreve a anterior)</span>
            )}
          </label>
        ))}
      </div>
      <div className="card">
        <h3>Elegíveis aguardando resposta</h3>
        {grupos.aguardando.length === 0 && <p className="muted">Nenhum.</p>}
        {grupos.aguardando.map((l) => (
          <p key={l.candidatoId}>
            {l.nomeExibicao || l.candidatoId} — Aguardando resposta
          </p>
        ))}
      </div>
      <div className="card">
        <h3>Inelegíveis</h3>
        {grupos.inelegiveis.map((l) => (
          <div key={l.candidatoId}>
            <span className="tag bad">Inelegível</span> {l.nomeExibicao || l.candidatoId}
            {(l.decisao?.motivos || []).map((m) => (
              <div key={m.mensagem} className="muted">
                {m.mensagem}
              </div>
            ))}
          </div>
        ))}
      </div>
      <button className="btn" type="button" disabled={!pode} onClick={() => setConfirmar(true)}>
        Revisar lote e avaliar
      </button>
      {!pode && <p className="muted">O botão explica o que falta acima. Sem chamada de rede até confirmar o envio.</p>}

      {confirmar && (
        <div className="modal-bg">
          <div className="modal">
            <h3>Confirmar envio</h3>
            <p>
              Esta execução envia {selecionados.length} candidato(s) ao modelo, um por chamada. Quem está inelegível,
              aguardando resposta ou desmarcado não será enviado.
            </p>
            <p className="muted">Modelo: {lote.llm.modelo || "(não configurado)"}</p>
            <ul>
              {selecionados.map((id) => {
                const l = lote.linhas.find((x) => x.candidatoId === id);
                return <li key={id}>{l?.nomeExibicao || id}</li>;
              })}
            </ul>
            <div className="row">
              <button className="btn" type="button" disabled={enviando} onClick={enviar}>
                {enviando ? "Enviando…" : "Confirmar envio"}
              </button>
              <button className="btn sec" type="button" disabled={enviando} onClick={() => setConfirmar(false)}>
                Voltar
              </button>
            </div>
            {erro && <p className="err">{erro}</p>}
          </div>
        </div>
      )}
    </>
  );
}
