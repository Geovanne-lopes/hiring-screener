import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiSend } from "../api";
import { formasQueTambemEntram, palavrasComparadas } from "../comparacao";
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

function completar(bruto: CriteriosDet): CriteriosDet {
  return {
    cargos: {
      ativo: Boolean(bruto.cargos?.ativo),
      aceitos: bruto.cargos?.aceitos ?? [],
      bloqueados: bruto.cargos?.bloqueados ?? [],
    },
    empresas: {
      ativo: Boolean(bruto.empresas?.ativo),
      bloqueadas: bruto.empresas?.bloqueadas ?? [],
    },
    idade: {
      ativo: Boolean(bruto.idade?.ativo),
      minima: bruto.idade?.minima ?? null,
      maxima: bruto.idade?.maxima ?? null,
    },
    escolaridade: {
      ativo: Boolean(bruto.escolaridade?.ativo),
      configuracao: {
        modelo: bruto.escolaridade?.configuracao?.modelo ?? "lista_valores_aceitos",
        aceitos: bruto.escolaridade?.configuracao?.aceitos ?? [],
      },
    },
  };
}

type ListaCampo = "aceitos" | "bloqueados" | "empresas" | "esc";

function ItemCargo({ item }: { item: string }) {
  const formas = formasQueTambemEntram(item);
  return (
    <span>
      {item}
      <span className="comp">comparado: {palavrasComparadas(item).join(" ")}</span>
      {formas.length > 0 && <span className="comp">também entra: {formas.join(", ")}</span>}
    </span>
  );
}

export default function Criterios() {
  const { projetoId } = useParams();
  const [c, setC] = useState<CriteriosDet | null>(null);
  const [novoCargo, setNovoCargo] = useState("");
  const [novoBloqueado, setNovoBloqueado] = useState("");
  const [novaEmpresa, setNovaEmpresa] = useState("");
  const [novaEsc, setNovaEsc] = useState("");
  const [aviso, setAviso] = useState("");
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");

  useEffect(() => {
    if (!projetoId) return;
    apiGet<Projeto>(`/api/projetos/${projetoId}`)
      .then((p) => setC(completar(p.criteriosDeterministicos)))
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

  function textoNovo(tipo: ListaCampo) {
    if (tipo === "aceitos") return novoCargo;
    if (tipo === "bloqueados") return novoBloqueado;
    if (tipo === "empresas") return novaEmpresa;
    return novaEsc;
  }

  function listaAtual(tipo: ListaCampo) {
    if (tipo === "aceitos") return criterios.cargos.aceitos;
    if (tipo === "bloqueados") return criterios.cargos.bloqueados;
    if (tipo === "empresas") return criterios.empresas.bloqueadas;
    return criterios.escolaridade.configuracao.aceitos;
  }

  function gravarLista(tipo: ListaCampo, aceitos: string[], limpar: boolean) {
    if (tipo === "aceitos") {
      setC({ ...criterios, cargos: { ...criterios.cargos, aceitos } });
      if (limpar) setNovoCargo("");
    } else if (tipo === "bloqueados") {
      setC({ ...criterios, cargos: { ...criterios.cargos, bloqueados: aceitos } });
      if (limpar) setNovoBloqueado("");
    } else if (tipo === "empresas") {
      setC({ ...criterios, empresas: { ...criterios.empresas, bloqueadas: aceitos } });
      if (limpar) setNovaEmpresa("");
    } else {
      setC({
        ...criterios,
        escolaridade: {
          ...criterios.escolaridade,
          configuracao: { ...criterios.escolaridade.configuracao, aceitos },
        },
      });
      if (limpar) setNovaEsc("");
    }
  }

  function addLista(tipo: ListaCampo) {
    const novos = separarLista(textoNovo(tipo));
    if (novos.length === 0) {
      setAviso("Item vazio ignorado.");
      return;
    }
    const aceitos = [...listaAtual(tipo)];
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
    gravarLista(tipo, aceitos, true);
  }

  function remover(tipo: ListaCampo, idx: number) {
    gravarLista(
      tipo,
      listaAtual(tipo).filter((_, i) => i !== idx),
      false,
    );
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
  if (c.cargos.ativo && c.cargos.aceitos.length === 0 && c.cargos.bloqueados.length === 0) {
    incompletos.push("cargos aceitos e bloqueados");
  }
  if (c.empresas.ativo && c.empresas.bloqueadas.length === 0) incompletos.push("empresas bloqueadas");
  if (c.idade.ativo && (c.idade.minima == null || c.idade.maxima == null)) incompletos.push("faixa de idade");
  if (c.escolaridade.ativo && c.escolaridade.configuracao.aceitos.length === 0) incompletos.push("escolaridade");

  return (
    <>
      <h2>Critérios duros</h2>
      {erro && <p className="err">{erro}</p>}
      {aviso && <p className="warn">{aviso}</p>}
      {ok && <p className="ok">{ok}</p>}
      {incompletos.length > 0 && (
        <p className="warn">Rascunho incompleto (não bloqueia o save): falta {incompletos.join(", ")}.</p>
      )}

      <div className="card">
        <h3>Cargos aceitos</h3>
        <p className="muted">
          A comparação ignora maiúsculas, acentos e espaços extras. Uma frase aceita entra se as palavras dela
          aparecerem seguidas no cargo. Masculino e feminino se equivalem. As únicas abreviações automáticas são Sr, Pl
          e Jr. O cargo não é reduzido à primeira palavra e não é traduzido para o inglês.
        </p>
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
              <ItemCargo item={item} />
              <button className="btn sec" type="button" onClick={() => remover("aceitos", i)}>
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
          <button className="btn sec" type="button" onClick={() => addLista("aceitos")}>
            Incluir
          </button>
        </div>

        <h3>Cargos bloqueados</h3>
        <p className="muted">
          Se o cargo contiver um destes termos, a pessoa fica inelegível, mesmo que o cargo também esteja na lista de
          aceitos.
        </p>
        <ul className="list">
          {c.cargos.bloqueados.map((item, i) => (
            <li key={item + i}>
              <ItemCargo item={item} />
              <button className="btn sec" type="button" onClick={() => remover("bloqueados", i)}>
                Remover
              </button>
            </li>
          ))}
        </ul>
        <div className="row">
          <textarea
            className="lista-cola"
            value={novoBloqueado}
            onChange={(e) => setNovoBloqueado(e.target.value)}
            placeholder={"Sênior\nPleno"}
          />
          <button className="btn sec" type="button" onClick={() => addLista("bloqueados")}>
            Incluir
          </button>
        </div>
      </div>

      <div className="card">
        <h3>Empresas bloqueadas</h3>
        <p className="muted">
          Se a empresa contiver um destes nomes, a pessoa fica inelegível. Maiúsculas, acentos e o sufixo S.A. não
          impedem o encontro.
        </p>
        <label className="switch">
          <input
            type="checkbox"
            checked={c.empresas.ativo}
            onChange={(e) => setC({ ...criterios, empresas: { ...criterios.empresas, ativo: e.target.checked } })}
          />
          Ativo
        </label>
        <ul className="list">
          {c.empresas.bloqueadas.map((item, i) => (
            <li key={item + i}>
              <span>
                {item}
                <span className="comp">comparado: {palavrasComparadas(item).join(" ")}</span>
              </span>
              <button className="btn sec" type="button" onClick={() => remover("empresas", i)}>
                Remover
              </button>
            </li>
          ))}
        </ul>
        <div className="row">
          <textarea
            className="lista-cola"
            value={novaEmpresa}
            onChange={(e) => setNovaEmpresa(e.target.value)}
            placeholder={"Cielo"}
          />
          <button className="btn sec" type="button" onClick={() => addLista("empresas")}>
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
        <p className="muted">
          37 Anos, 37 - Anos, 37 Años e 37 anos e 2 meses contam como 37. Os meses não entram na conta.
        </p>
        <div className="row">
          <div>
            <label>Idade mínima</label>
            <input
              type="number"
              value={c.idade.minima ?? ""}
              onChange={(e) =>
                setC({
                  ...criterios,
                  idade: { ...criterios.idade, minima: e.target.value === "" ? null : Number(e.target.value) },
                })
              }
            />
          </div>
          <div>
            <label>Idade máxima</label>
            <input
              type="number"
              value={c.idade.maxima ?? ""}
              onChange={(e) =>
                setC({
                  ...criterios,
                  idade: { ...criterios.idade, maxima: e.target.value === "" ? null : Number(e.target.value) },
                })
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
            onChange={(e) =>
              setC({ ...criterios, escolaridade: { ...criterios.escolaridade, ativo: e.target.checked } })
            }
          />
          Ativo
        </label>
        <p className="muted">
          A frase aceita entra se as palavras dela aparecerem seguidas na célula. Maiúsculas e acentos são ignorados.
          Não há abreviação automática nem tradução.
        </p>
        <ul className="list">
          {c.escolaridade.configuracao.aceitos.map((item, i) => (
            <li key={item + i}>
              <span>
                {item}
                <span className="comp">comparado: {palavrasComparadas(item).join(" ")}</span>
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
