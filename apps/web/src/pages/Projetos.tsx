import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet, apiSend } from "../api";
import type { Projeto } from "../types";

export default function Projetos() {
  const nav = useNavigate();
  const [lista, setLista] = useState<Projeto[]>([]);
  const [nome, setNome] = useState("");
  const [editarId, setEditarId] = useState<string | null>(null);
  const [editarNome, setEditarNome] = useState("");
  const [dupId, setDupId] = useState<string | null>(null);
  const [dupNome, setDupNome] = useState("");
  const [erro, setErro] = useState("");

  function carregar() {
    apiGet<Projeto[]>("/api/projetos")
      .then(setLista)
      .catch((e) => setErro(e.message));
  }

  useEffect(() => {
    carregar();
  }, []);

  async function criar() {
    setErro("");
    try {
      const p = await apiSend<Projeto>("/api/projetos", "POST", { nome });
      setNome("");
      nav(`/projetos/${p.projetoId}/criterios`);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  async function salvarNome(id: string) {
    setErro("");
    try {
      await apiSend(`/api/projetos/${id}`, "PATCH", { nome: editarNome });
      setEditarId(null);
      carregar();
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  async function duplicar(id: string) {
    setErro("");
    try {
      const p = await apiSend<Projeto>(`/api/projetos/${id}/duplicar`, "POST", { nome: dupNome });
      setDupId(null);
      nav(`/projetos/${p.projetoId}/criterios`);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  return (
    <>
      <h2>Projetos</h2>
      <p className="lead">Uma vaga ou processo. Duplicar copia os critérios duros e a job description vigente, sem o lote.</p>
      {erro && <p className="err">{erro}</p>}
      <div className="card">
        <label htmlFor="novo">Criar projeto</label>
        <div className="row">
          <input id="novo" value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Nome da vaga" />
          <button className="btn" type="button" onClick={criar}>
            Criar
          </button>
        </div>
      </div>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Atualizado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((p) => (
              <tr key={p.projetoId}>
                <td>
                  {editarId === p.projetoId ? (
                    <div className="row">
                      <input value={editarNome} onChange={(e) => setEditarNome(e.target.value)} />
                      <button className="btn" type="button" onClick={() => salvarNome(p.projetoId)}>
                        Salvar nome
                      </button>
                    </div>
                  ) : (
                    p.nome
                  )}
                </td>
                <td className="muted">{p.atualizadoEm}</td>
                <td>
                  <div className="row">
                    <button className="btn" type="button" onClick={() => nav(`/projetos/${p.projetoId}/criterios`)}>
                      Abrir
                    </button>
                    <button
                      className="btn sec"
                      type="button"
                      onClick={() => {
                        setEditarId(p.projetoId);
                        setEditarNome(p.nome);
                      }}
                    >
                      Editar nome
                    </button>
                    <button
                      className="btn sec"
                      type="button"
                      onClick={() => {
                        setDupId(p.projetoId);
                        setDupNome(`${p.nome} (cópia)`);
                      }}
                    >
                      Duplicar
                    </button>
                  </div>
                  {dupId === p.projetoId && (
                    <div className="row" style={{ marginTop: 8 }}>
                      <input value={dupNome} onChange={(e) => setDupNome(e.target.value)} />
                      <button className="btn" type="button" onClick={() => duplicar(p.projetoId)}>
                        Confirmar duplicação
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
