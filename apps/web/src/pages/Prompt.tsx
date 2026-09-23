import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiSend } from "../api";

type Versao = {
  promptId: string;
  versao: number;
  criadoEm: string | null;
  criteriosQualitativosVersaoId: string;
  template: string;
};

export default function Prompt() {
  const { projetoId } = useParams();
  const [template, setTemplate] = useState("");
  const [inicial, setInicial] = useState("");
  const [versoes, setVersoes] = useState<Versao[]>([]);
  const [preview, setPreview] = useState("");
  const [candId, setCandId] = useState("");
  const [cands, setCands] = useState<Array<{ candidatoId: string; nomeExibicao: string | null; linhaOrigem: number }>>(
    [],
  );
  const [msgPreview, setMsgPreview] = useState("");
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");

  useEffect(() => {
    if (!projetoId) return;
    apiGet<{
      vigente: { template: string } | null;
      templateInicial: string;
      versoes: Versao[];
    }>(`/api/projetos/${projetoId}/prompt`)
      .then((r) => {
        setInicial(r.templateInicial);
        setTemplate(r.vigente?.template || r.templateInicial);
        setVersoes(r.versoes);
      })
      .catch((e) => setErro(e.message));
  }, [projetoId]);

  async function salvar() {
    setErro("");
    setOk("");
    try {
      const r = await apiSend<{ promptId: string; versao: number }>(`/api/projetos/${projetoId}/prompt`, "PUT", {
        template,
      });
      setOk(`Prompt salvo: ${r.promptId} (versão ${r.versao}).`);
      const novamente = await apiGet<{ versoes: Versao[] }>(`/api/projetos/${projetoId}/prompt`);
      setVersoes(novamente.versoes);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  async function montarPreview(id?: string) {
    setErro("");
    try {
      const r = await apiSend<{
        texto: string;
        mensagem?: string;
        candidatoId?: string;
        candidatos?: Array<{ candidatoId: string; nomeExibicao: string | null; linhaOrigem: number }>;
      }>(`/api/projetos/${projetoId}/prompt/preview`, "POST", { candidatoId: id || candId || null });
      setPreview(r.texto);
      setMsgPreview(r.mensagem || "");
      if (r.candidatos) setCands(r.candidatos);
      if (r.candidatoId) setCandId(r.candidatoId);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  return (
    <>
      <h2>Prompt do projeto</h2>
      <p className="lead">Template editável. Salvar gera versão nova. Pré-visualizar não chama o modelo.</p>
      {erro && <p className="err">{erro}</p>}
      {ok && <p className="ok">{ok}</p>}
      <div className="card">
        <textarea value={template} onChange={(e) => setTemplate(e.target.value)} />
        <div className="row" style={{ marginTop: 8 }}>
          <button className="btn" type="button" onClick={salvar}>
            Salvar prompt (nova versão)
          </button>
          <button className="btn sec" type="button" onClick={() => setTemplate(inicial)}>
            Restaurar texto inicial no editor
          </button>
        </div>
      </div>
      <div className="card">
        <h3>Pré-visualização</h3>
        <div className="row">
          <select
            value={candId}
            onChange={(e) => {
              setCandId(e.target.value);
              montarPreview(e.target.value);
            }}
          >
            <option value="">Selecione um elegível com resposta</option>
            {cands.map((c) => (
              <option key={c.candidatoId} value={c.candidatoId}>
                {c.nomeExibicao || c.candidatoId} (linha {c.linhaOrigem})
              </option>
            ))}
          </select>
          <button className="btn sec" type="button" onClick={() => montarPreview()}>
            Montar pré-visualização
          </button>
        </div>
        {msgPreview && <p className="muted">{msgPreview}</p>}
        {preview && <pre className="preview">{preview}</pre>}
      </div>
      <div className="card">
        <h3>Versões anteriores</h3>
        <p className="muted">Só leitura. Restaurar copia para o editor; salvar gera versão nova.</p>
        <ul className="list">
          {versoes.map((v) => (
            <li key={v.promptId}>
              <span>
                {v.promptId} · v{v.versao} · {v.criadoEm}
              </span>
              <button className="btn sec" type="button" onClick={() => setTemplate(v.template)}>
                Copiar para o editor
              </button>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
