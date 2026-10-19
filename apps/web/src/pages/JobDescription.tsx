import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiForm, apiGet, apiSend } from "../api";

type Versao = {
  jobDescriptionId: string;
  versao: number;
  texto: string;
  criadoEm: string | null;
};

type Resposta = {
  vigente: Versao | null;
  versoes: Versao[];
  aviso: string | null;
};

export default function JobDescription() {
  const { projetoId } = useParams();
  const [texto, setTexto] = useState("");
  const [encoding, setEncoding] = useState("utf-8");
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [vigente, setVigente] = useState<Versao | null>(null);
  const [versoes, setVersoes] = useState<Versao[]>([]);
  const [aviso, setAviso] = useState<string | null>(null);
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");

  function aplicar(r: Resposta, preencherEditor: boolean) {
    setVigente(r.vigente);
    setVersoes(r.versoes);
    setAviso(r.aviso);
    if (preencherEditor) setTexto(r.vigente?.texto ?? "");
  }

  useEffect(() => {
    if (!projetoId) return;
    apiGet<Resposta>(`/api/projetos/${projetoId}/job-description`)
      .then((r) => aplicar(r, true))
      .catch((e) => setErro(e.message));
  }, [projetoId]);

  async function enviarArquivo() {
    setErro("");
    setOk("");
    if (!arquivo) {
      setErro("Selecione um arquivo .txt, .md ou .docx.");
      return;
    }
    const fd = new FormData();
    fd.append("arquivo", arquivo);
    fd.append("encoding", encoding);
    try {
      const r = await apiForm<{ texto: string }>(`/api/projetos/${projetoId}/job-description/arquivo`, fd);
      setTexto(r.texto);
      setOk("Texto carregado no editor. Ainda não está vigente.");
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  async function salvar() {
    setErro("");
    setOk("");
    try {
      const r = await apiSend<Versao & { aviso: string | null }>(
        `/api/projetos/${projetoId}/job-description`,
        "PUT",
        { texto },
      );
      setOk(`Job description salva: ${r.jobDescriptionId} (versão ${r.versao}).`);
      const novamente = await apiGet<Resposta>(`/api/projetos/${projetoId}/job-description`);
      aplicar(novamente, true);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  return (
    <>
      <h2>Job description</h2>
      <p className="lead">
        Esta descrição é o contexto geral da vaga. A IA recebe este texto na variável do prompt e usa isso para ler as
        respostas. Cargo, idade e escolaridade continuam na triagem e não são rejulgados aqui.
      </p>
      {erro && <p className="err">{erro}</p>}
      {ok && <p className="ok">{ok}</p>}
      {aviso && <p className="warn">{aviso}</p>}
      <div className="card">
        <p className="muted">
          {vigente
            ? `Vigente: versão ${vigente.versao} (${vigente.jobDescriptionId}).`
            : "Nenhuma job description salva. A triagem determinística segue sem este texto."}
        </p>
        <textarea value={texto} onChange={(e) => setTexto(e.target.value)} />
        <div className="row" style={{ marginTop: 8 }}>
          <button className="btn" type="button" onClick={salvar}>
            Salvar job description
          </button>
        </div>
      </div>
      <div className="card">
        <h3>Enviar arquivo</h3>
        <p className="muted">O envio só preenche o editor. A versão vigente muda ao salvar.</p>
        <div className="row">
          <input
            type="file"
            accept=".txt,.md,.docx,.pdf"
            onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
          />
          <label>
            Encoding de .txt e .md{" "}
            <select value={encoding} onChange={(e) => setEncoding(e.target.value)}>
              <option value="utf-8">utf-8</option>
              <option value="latin-1">latin-1</option>
            </select>
          </label>
          <button className="btn sec" type="button" onClick={enviarArquivo}>
            Enviar arquivo
          </button>
        </div>
        <p className="muted">.docx não usa encoding. PDF e outras extensões são recusados.</p>
      </div>
      <div className="card">
        <h3>Versões</h3>
        {versoes.length === 0 && <p className="muted">Nenhuma versão gravada.</p>}
        {versoes.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Versão</th>
                <th>Id</th>
                <th>Criada em</th>
                <th>Texto</th>
              </tr>
            </thead>
            <tbody>
              {versoes.map((v) => (
                <tr key={v.jobDescriptionId}>
                  <td>
                    {v.versao}
                    {vigente?.jobDescriptionId === v.jobDescriptionId ? " · vigente" : ""}
                  </td>
                  <td>{v.jobDescriptionId}</td>
                  <td>{v.criadoEm}</td>
                  <td>
                    <pre className="preview">{v.texto}</pre>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
