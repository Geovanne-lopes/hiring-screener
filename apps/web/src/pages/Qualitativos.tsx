import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiSend } from "../api";
import type { ItemQual } from "../types";

export default function Qualitativos() {
  const { projetoId } = useParams();
  const [itens, setItens] = useState<ItemQual[]>([]);
  const [versao, setVersao] = useState<string | null>(null);
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");
  const [confirmacao, setConfirmacao] = useState<string | null>(null);

  function carregar() {
    apiGet<{ versaoId: string | null; itens: ItemQual[] }>(`/api/projetos/${projetoId}/criterios-qualitativos`)
      .then((r) => {
        setItens(r.itens || []);
        setVersao(r.versaoId);
      })
      .catch((e) => setErro(e.message));
  }

  useEffect(() => {
    carregar();
  }, [projetoId]);

  function atualizar(i: number, patch: Partial<ItemQual>) {
    setItens(itens.map((item, idx) => (idx === i ? { ...item, ...patch } : item)));
  }

  function mover(i: number, dir: -1 | 1) {
    const j = i + dir;
    if (j < 0 || j >= itens.length) return;
    const copia = [...itens];
    const tmp = copia[i];
    copia[i] = copia[j];
    copia[j] = tmp;
    setItens(copia.map((item, idx) => ({ ...item, ordem: idx + 1 })));
  }

  async function salvar(confirmarRegraDura = false) {
    setErro("");
    setOk("");
    setConfirmacao(null);
    try {
      const r = await apiSend<{
        precisaConfirmacao?: boolean;
        aviso?: string;
        versaoId?: string;
        itens?: ItemQual[];
        avisos?: string[];
      }>(`/api/projetos/${projetoId}/criterios-qualitativos`, "PUT", {
        itens: itens.map((item, i) => ({ ...item, ordem: i + 1 })),
        confirmarRegraDura,
      });
      if (r.precisaConfirmacao) {
        setConfirmacao(r.aviso || "");
        return;
      }
      setVersao(r.versaoId || null);
      if (r.itens) setItens(r.itens);
      setOk(`Critérios qualitativos salvos (${r.versaoId}).`);
      if (r.avisos?.length) setErro(r.avisos.join(" "));
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  return (
    <>
      <h2>Critérios qualitativos da vaga</h2>
      <p className="warn">
        Cargo, idade e escolaridade já foram aplicados na triagem. Não cadastre esses critérios aqui para o modelo
        decidir quem entra. O modelo não reabre a porta de entrada.
      </p>
      {erro && <p className="err">{erro}</p>}
      {ok && <p className="ok">{ok}</p>}
      {versao && <p className="muted">Versão vigente: {versao}</p>}
      {itens.length === 0 && <p>Adicione o primeiro critério qualitativo. Não há disparo de LLM nesta tela.</p>}
      {itens.map((item, i) => (
        <div className="card" key={item.criterioId || i}>
          <label>Nome</label>
          <input value={item.nome} onChange={(e) => atualizar(i, { nome: e.target.value })} />
          <label>Descrição (o que conta como atendimento)</label>
          <textarea value={item.descricao} onChange={(e) => atualizar(i, { descricao: e.target.value })} />
          <label className="switch">
            <input
              type="checkbox"
              checked={item.eliminatorio}
              onChange={(e) => atualizar(i, { eliminatorio: e.target.checked })}
            />
            Eliminatório
          </label>
          <div className="row">
            <button className="btn sec" type="button" onClick={() => mover(i, -1)}>
              Subir
            </button>
            <button className="btn sec" type="button" onClick={() => mover(i, 1)}>
              Descer
            </button>
            <button className="btn danger" type="button" onClick={() => setItens(itens.filter((_, idx) => idx !== i))}>
              Remover
            </button>
          </div>
        </div>
      ))}
      <div className="row">
        <button
          className="btn sec"
          type="button"
          onClick={() =>
            setItens([...itens, { nome: "", descricao: "", ordem: itens.length + 1, eliminatorio: false }])
          }
        >
          Adicionar critério
        </button>
        <button className="btn" type="button" onClick={() => salvar(false)}>
          Salvar critérios
        </button>
      </div>
      {confirmacao && (
        <div className="modal-bg">
          <div className="modal">
            <p>{confirmacao}</p>
            <div className="row">
              <button className="btn" type="button" onClick={() => salvar(true)}>
                Confirmar mesmo assim
              </button>
              <button className="btn sec" type="button" onClick={() => setConfirmacao(null)}>
                Voltar ao editor
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
