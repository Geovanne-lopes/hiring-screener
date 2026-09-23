import { useState } from "react";
import { useParams } from "react-router-dom";
import { apiForm } from "../api";
import type { Mapeamento } from "../types";

type Preview = {
  colunas: string[];
  linhas: Record<string, string>[];
  sugestaoUltimoCargo: string | null;
  xlsx: boolean;
};

const mapaVazio = (): Mapeamento => ({
  ultimoCargo: null,
  idade: null,
  escolaridade: null,
  nomeExibicao: null,
  respostasChatbot: [],
  cidade: null,
  statusLegado: null,
});

export default function Importar() {
  const { projetoId } = useParams();
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [encoding, setEncoding] = useState("latin-1");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [mapa, setMapa] = useState<Mapeamento>(mapaVazio());
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");

  async function gerarPreview() {
    setErro("");
    setOk("");
    if (!arquivo) {
      setErro("Selecione um arquivo CSV ou XLSX para importar.");
      return;
    }
    const fd = new FormData();
    fd.append("arquivo", arquivo);
    fd.append("encoding", encoding);
    try {
      const p = await apiForm<Preview>(`/api/projetos/${projetoId}/importacao/preview`, fd);
      setPreview(p);
      setMapa((m) => ({
        ...m,
        ultimoCargo: m.ultimoCargo || p.sugestaoUltimoCargo,
      }));
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  async function confirmar() {
    setErro("");
    setOk("");
    if (!arquivo) {
      setErro("Selecione um arquivo CSV ou XLSX para importar.");
      return;
    }
    const fd = new FormData();
    fd.append("arquivo", arquivo);
    fd.append("encoding", encoding);
    fd.append("mapeamento_json", JSON.stringify(mapa));
    try {
      const r = await apiForm<{ quantidade: number }>(`/api/projetos/${projetoId}/importacao/confirmar`, fd);
      setOk(`Importação confirmada: ${r.quantidade} candidato(s). A triagem não rodou sozinha.`);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  function setCampo(campo: keyof Mapeamento, valor: string) {
    setMapa({ ...mapa, [campo]: valor || null });
  }

  function toggleResp(col: string) {
    const tem = mapa.respostasChatbot.includes(col);
    setMapa({
      ...mapa,
      respostasChatbot: tem ? mapa.respostasChatbot.filter((c) => c !== col) : [...mapa.respostasChatbot, col],
    });
  }

  const xlsx = arquivo?.name.toLowerCase().endsWith(".xlsx") || arquivo?.name.toLowerCase().endsWith(".xlsm");

  return (
    <>
      <h2>Importar planilha</h2>
      <p className="lead">CSV ou XLSX. A importação só segue depois de confirmar o mapeamento.</p>
      {erro && <p className="err">{erro}</p>}
      {ok && <p className="ok">{ok}</p>}
      <div className="card">
        <label>Arquivo</label>
        <input
          type="file"
          accept=".csv,.xlsx,.xlsm"
          onChange={(e) => {
            setArquivo(e.target.files?.[0] || null);
            setPreview(null);
            setOk("");
          }}
        />
        <label style={{ marginTop: 8 }}>Encoding (CSV)</label>
        <select value={encoding} disabled={xlsx} onChange={(e) => setEncoding(e.target.value)}>
          <option value="latin-1">latin-1 (padrão)</option>
          <option value="utf-8">utf-8</option>
        </select>
        <p className="muted">Padrão latin-1, como o legado. XLSX ignora encoding.</p>
        <button className="btn sec" type="button" onClick={gerarPreview}>
          Pré-visualizar
        </button>
      </div>
      {preview && (
        <>
          <div className="card">
            <h3>Pré-visualização (até 5 linhas)</h3>
            <div style={{ overflow: "auto" }}>
              <table>
                <thead>
                  <tr>
                    {preview.colunas.map((c) => (
                      <th key={c}>{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.linhas.map((lin, i) => (
                    <tr key={i}>
                      {preview.colunas.map((c) => (
                        <td key={c}>{lin[c]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card">
            <h3>Mapeamento</h3>
            {preview.sugestaoUltimoCargo && (
              <p className="muted">
                Coluna sugerida para último cargo: {preview.sugestaoUltimoCargo}. Confirme ou escolha outra. Cargo
                Anterior não é sugerido.
              </p>
            )}
            {(
              [
                ["ultimoCargo", "Último cargo"],
                ["idade", "Idade"],
                ["escolaridade", "Escolaridade"],
                ["nomeExibicao", "Nome (rótulo, opcional)"],
                ["cidade", "Cidade (metadado)"],
                ["statusLegado", "Status legado (metadado)"],
              ] as Array<[keyof Mapeamento, string]>
            ).map(([campo, label]) => (
              <div key={campo} style={{ marginBottom: 8 }}>
                <label>{label}</label>
                <select
                  value={(mapa[campo] as string) || ""}
                  onChange={(e) => setCampo(campo, e.target.value)}
                >
                  <option value="">—</option>
                  {preview.colunas.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            ))}
            <p>Respostas de chatbot (uma ou mais colunas; sem nome prescrito)</p>
            {preview.colunas.map((c) => (
              <label key={c} className="switch">
                <input
                  type="checkbox"
                  checked={mapa.respostasChatbot.includes(c)}
                  onChange={() => toggleResp(c)}
                />
                {c}
              </label>
            ))}
            <button className="btn" type="button" onClick={confirmar}>
              Confirmar mapeamento e importar
            </button>
          </div>
        </>
      )}
    </>
  );
}
