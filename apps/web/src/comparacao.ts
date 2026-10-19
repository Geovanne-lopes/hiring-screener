/** Espelho de apps/api/triagem/comparacao.py para a tela. Sem modelo. */

const SEPARADORES = ["/", "|", "-", "–", "—", ",", ";"];

const ALIAS: Record<string, string[]> = {
  senior: ["Sênior", "Senior", "Sr", "Sr."],
  sr: ["Sênior", "Senior", "Sr", "Sr."],
  pleno: ["Pleno", "Plena", "Pl", "Pl."],
  plena: ["Pleno", "Plena", "Pl", "Pl."],
  pl: ["Pleno", "Plena", "Pl", "Pl."],
  junior: ["Júnior", "Junior", "Jr", "Jr."],
  jr: ["Júnior", "Junior", "Jr", "Jr."],
};

const ANO = new Set(["ano", "anos", "year", "years"]);
const MES = new Set(["mes", "meses", "month", "months"]);

export function normalizarTexto(texto: string): string {
  return texto
    .trim()
    .replace(/\s+/g, " ")
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
}

function semPontas(token: string): string {
  return token.replace(/^\.+|\.+$/g, "");
}

export function palavrasComparadas(texto: string): string[] {
  let base = normalizarTexto(texto);
  for (const separador of SEPARADORES) {
    base = base.split(separador).join(" ");
  }
  return base
    .split(/\s+/)
    .map(semPontas)
    .filter((token) => token.length > 0);
}

function varianteGenero(token: string): string | null {
  if (token.length >= 7 && token.endsWith("ora")) {
    const miolo = token.slice(0, -3);
    if (miolo.length >= 4) return `${miolo}or`;
  }
  if (token.length >= 6 && token.endsWith("or")) {
    const miolo = token.slice(0, -2);
    if (miolo.length >= 4) return `${miolo}ora`;
  }
  if (token.length >= 5 && (token.endsWith("o") || token.endsWith("a"))) {
    const miolo = token.slice(0, -1);
    if (miolo.length >= 4) return miolo + (token.endsWith("o") ? "a" : "o");
  }
  return null;
}

function generoNoOriginal(palavra: string, chave: string, outra: string): string | null {
  const original = palavra.toLowerCase();
  if (chave.endsWith("ora") && outra.endsWith("or") && original.endsWith("ora")) {
    return `${palavra.slice(0, -3)}or`;
  }
  if (chave.endsWith("or") && outra.endsWith("ora") && original.endsWith("or")) {
    return `${palavra}a`;
  }
  if (chave.endsWith("o") && outra.endsWith("a") && original.endsWith("o")) {
    return `${palavra.slice(0, -1)}a`;
  }
  if (chave.endsWith("a") && outra.endsWith("o") && original.endsWith("a")) {
    return `${palavra.slice(0, -1)}o`;
  }
  return null;
}

function visivel(forma: string, digitada: string): boolean {
  const semPonto = semPontas(digitada);
  const formas = new Set([digitada.toLowerCase(), semPonto.toLowerCase()]);
  return !formas.has(forma.toLowerCase());
}

function variantesDaPalavra(palavra: string): string[] {
  const chave = semPontas(normalizarTexto(palavra));
  const digitada = palavra.trim();
  const alias = ALIAS[chave];
  if (alias) return alias.filter((forma) => visivel(forma, digitada));
  const outra = varianteGenero(chave);
  if (!outra) return [];
  const exibicao = generoNoOriginal(semPontas(digitada), chave, outra);
  if (exibicao && visivel(exibicao, digitada)) return [exibicao];
  return [];
}

function partirOriginal(texto: string): string[] {
  let base = texto.trim().replace(/\s+/g, " ");
  for (const separador of SEPARADORES) {
    base = base.split(separador).join(" ");
  }
  return base
    .split(/\s+/)
    .map(semPontas)
    .filter((token) => token.length > 0);
}

export function formasQueTambemEntram(texto: string): string[] {
  const origem = partirOriginal(texto);
  if (origem.length === 0) return [];
  const formas: string[] = [];
  const vistas = new Set<string>();
  const digitada = texto.trim().replace(/\s+/g, " ").toLowerCase();
  origem.forEach((palavra, indice) => {
    for (const variante of variantesDaPalavra(palavra)) {
      const copia = [...origem];
      copia[indice] = variante;
      const frase = copia.join(" ");
      const chave = frase.toLowerCase();
      if (vistas.has(chave) || chave === digitada) continue;
      vistas.add(chave);
      formas.push(frase);
    }
  });
  return formas;
}

function naFaixa(numero: number): string | null {
  if (numero >= 1 && numero <= 120) return String(numero);
  return null;
}

export function idadeComparada(valor: string): string | null {
  const texto = valor.trim().replace(/\s+/g, " ");
  if (!texto || normalizarTexto(valor) === "#name?") return null;
  const puro = texto.match(/^(\d+)(?:[.,](\d+))?$/);
  if (puro) {
    if (puro[2] !== undefined && Number(puro[2]) !== 0) return null;
    return naFaixa(Number(puro[1]));
  }
  let bruto = normalizarTexto(texto);
  for (const separador of ["-", "–", "—", "+", "/", "|"]) {
    bruto = bruto.split(separador).join(" ");
  }
  bruto = bruto.replace(/(\d)([a-z])/g, "$1 $2").replace(/([a-z])(\d)/g, "$1 $2");
  const tokens = bruto.split(/\s+/).filter(Boolean);
  const inteiro = (token: string) => /^\d+$/.test(token);
  if (tokens.length === 2 && inteiro(tokens[0]) && ANO.has(tokens[1])) return naFaixa(Number(tokens[0]));
  if (
    tokens.length === 4 &&
    inteiro(tokens[0]) &&
    ANO.has(tokens[1]) &&
    inteiro(tokens[2]) &&
    MES.has(tokens[3])
  ) {
    return naFaixa(Number(tokens[0]));
  }
  if (
    tokens.length === 5 &&
    inteiro(tokens[0]) &&
    ANO.has(tokens[1]) &&
    tokens[2] === "e" &&
    inteiro(tokens[3]) &&
    MES.has(tokens[4])
  ) {
    return naFaixa(Number(tokens[0]));
  }
  return null;
}
