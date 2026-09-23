import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiSend } from "../api";
import type { CriteriosDet, Projeto } from "../types";

function comparado(texto: string) {
  return texto
    .trim()
    .replace(/\s+/g, " ")
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
}

function separarLista(texto: string): string[] {
  const bruto = texto.trim();
  if (!bruto) return [];
  const partes = bruto.includes("\n") ? bruto.split(/\r?\n/) : bruto.split(/[;,]/);
  const vistos = new Set<string>();
  const itens: string[] = [];
  for (const parte of partes) {
    const item = parte.trim().replace(/\s+/g, " ");
    if (!item) continue;
    const chave = comparado(item);
    if (vistos.has(chave)) continue;
    vistos.add(chave);
    itens.push(item);
  }
  return itens;
}

export default function Criterios() {
  const { projetoId } = useParams();
  const [c, setC] = useState<CriteriosDet | null>(null);
  const [novoCargo, setNovoCargo] = useState("");
  const [novaEsc, setNovaEsc] = useState("");
  const [aviso, setAviso] = useState("");
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");

  useEffect(() => {
    if (!projetoId) return;
    apiGet<Projeto>(`/api/projetos/${projetoId}`)
      .then((p) => setC(p.criteriosDeterministicos))
      .catch((e) => setErro(e.message));
  }, [projetoId]);

  if (!c) {
    return (
      <>
        <h2>Critérios duros</h2>
        {erro ? <p className="err">{erro}</p> : <p>Carregando…</p>}
      </>
    );
  }

  const criterios = c;

  function addLista(tipo: "cargo" | "esc") {
    const novos = separarLista(tipo === "cargo" ? novoCargo : novaEsc);
    if (novos.length === 0) {
      setAviso("Item vazio ignorado.");
      return;
    }
    const lista = tipo === "cargo" ? criterios.cargos.aceitos : criterios.escolaridade.configuracao.aceitos;
    const aceitos = [...lista];
    let incluidos = 0;
    let repetidos = 0;
    for (const valor of novos) {
      if (aceitos.some((x) => comparado(x) === comparado(valor))) {
        repetidos += 1;
        continue;
      }
      aceitos.push(valor);
      incluidos += 1;
    }
    const partes = [`${incluidos} incluído(s).`];
    if (repetidos > 0) partes.push(`${repetidos} já estava(m) na lista.`);
    setAviso(partes.join(" "));
    if (tipo === "cargo") {
      setC({ ...criterios, cargos: { ...criterios.cargos, aceitos } });
      setNovoCargo("");
    } else {
      setC({
        ...criterios,
        escolaridade: {
          ...criterios.escolaridade,
          configuracao: { ...criterios.escolaridade.configuracao, aceitos },
        },
      });
      setNovaEsc("");
    }
  }

  function remover(tipo: "cargo" | "esc", idx: number) {
    if (tipo === "cargo") {
      setC({
        ...criterios,
        cargos: { ...criterios.cargos, aceitos: criterios.cargos.aceitos.filter((_, i) => i !== idx) },
      });
    } else {
      setC({
        ...criterios,
        escolaridade: {
          ...criterios.escolaridade,
          configuracao: {
            ...criterios.escolaridade.configuracao,
            aceitos: criterios.escolaridade.configuracao.aceitos.filter((_, i) => i !== idx),
          },
        },
      });
    }
  }

  async function salvar() {
    setErro("");
    setOk("");
    try {
      const r = await apiSend<{ avisos: string[]; incompletos: string[]; criteriosVersao: string }>(
        `/api/projetos/${projetoId}/criterios-deterministicos`,
        "PUT",
        criterios,
      );
      setOk(`Critérios salvos (${r.criteriosVersao}).`);
      if (r.avisos?.length) setAviso(r.avisos.join(" "));
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  const incompletos: string[] = [];
  if (c.cargos.ativo && c.cargos.aceitos.length === 0) incompletos.push("cargos aceitos");
  if (c.idade.ativo && (c.idade.minima == null || c.idade.maxima == null)) incompletos.push("faixa de idade");
  if (c.escolaridade.ativo && c.escolaridade.configuracao.aceitos.length === 0) incompletos.push("escolaridade");

  return (
    <>
      <h2>Critérios duros</h2>
      <p className="lead">
        A comparação ignora maiúsculas, acentos e espaços extras. Não reduz o cargo à primeira palavra e não aplica
        sinônimos automáticos. Um complemento depois de /, | ou traço ainda conta como o cargo da lista: &quot;Analista
        de CRM Pleno / Martech&quot; entra se a lista tiver &quot;Analista de CRM Pleno&quot;.
      </p>
      {erro && <p className="err">{erro}</p>}
      {aviso && <p className="warn">{aviso}</p>}
      {ok && <p className="ok">{ok}</p>}
      {incompletos.length > 0 && (
        <p className="warn">Rascunho incompleto (não bloqueia o save): falta {incompletos.join(", ")}.</p>
      )}

      <div className="card">
        <h3>Cargos aceitos</h3>
        <label className="switch">
          <input
            type="checkbox"
            checked={c.cargos.ativo}
            onChange={(e) => setC({ ...criterios, cargos: { ...criterios.cargos, ativo: e.target.checked } })}
          />
          Ativo
        </label>
        <ul className="list">
          {c.cargos.aceitos.map((item, i) => (
            <li key={item + i}>
              <span>
                {item}
                <span className="comp">comparado: {comparado(item)}</span>
              </span>
              <button className="btn sec" type="button" onClick={() => remover("cargo", i)}>
                Remover
              </button>
            </li>
          ))}
        </ul>
        <p className="muted">Um cargo por linha, ou vários na mesma linha separados por vírgula ou ponto e vírgula.</p>
        <div className="row">
          <textarea
            className="lista-cola"
            value={novoCargo}
            onChange={(e) => setNovoCargo(e.target.value)}
            placeholder={"Analista de CRM Sênior\nAnalista de Dados Sênior"}
          />
          <button className="btn sec" type="button" onClick={() => addLista("cargo")}>
            Incluir
          </button>
        </div>
      </div>

      <div className="card">
        <h3>Faixa de idade</h3>
        <label className="switch">
          <input
            type="checkbox"
            checked={c.idade.ativo}
            onChange={(e) => setC({ ...criterios, idade: { ...criterios.idade, ativo: e.target.checked } })}
          />
          Ativo
        </label>
        <p className="muted">Os limites são inclusivos: a idade mínima e a máxima também são aceitas.</p>
        <div className="row">
          <div>
            <label>Idade mínima</label>
            <input
              type="number"
              value={c.idade.minima ?? ""}
              onChange={(e) =>
                setC({ ...criterios, idade: { ...criterios.idade, minima: e.target.value === "" ? null : Number(e.target.value) } })
              }
            />
          </div>
          <div>
            <label>Idade máxima</label>
            <input
              type="number"
              value={c.idade.maxima ?? ""}
              onChange={(e) =>
                setC({ ...criterios, idade: { ...criterios.idade, maxima: e.target.value === "" ? null : Number(e.target.value) } })
              }
            />
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Escolaridade</h3>
        <label className="switch">
          <input
            type="checkbox"
            checked={c.escolaridade.ativo}
            onChange={(e) => setC({ ...criterios, escolaridade: { ...criterios.escolaridade, ativo: e.target.checked } })}
          />
          Ativo
        </label>
        <p className="muted">
          A célula passa se contiver um item desta lista, depois de ignorar maiúsculas e acentos. Por exemplo, Bacharelado
          aceita &quot;Bacharelado · 2011 – 2014&quot;. O texto inteiro do Recruiter não precisa ser idêntico.
        </p>
        <ul className="list">
          {c.escolaridade.configuracao.aceitos.map((item, i) => (
            <li key={item + i}>
              <span>
                {item}
                <span className="comp">comparado: {comparado(item)}</span>
              </span>
              <button className="btn sec" type="button" onClick={() => remover("esc", i)}>
                Remover
              </button>
            </li>
          ))}
        </ul>
        <p className="muted">Uma escolaridade por linha, ou várias na mesma linha separadas por vírgula ou ponto e vírgula.</p>
        <div className="row">
          <textarea
            className="lista-cola"
            value={novaEsc}
            onChange={(e) => setNovaEsc(e.target.value)}
            placeholder={"Bacharelado\nSuperior Completo\nbachelor"}
          />
          <button className="btn sec" type="button" onClick={() => addLista("esc")}>
            Incluir
          </button>
        </div>
      </div>

      <button className="btn" type="button" onClick={salvar}>
        Salvar critérios
      </button>
    </>
  );
}
