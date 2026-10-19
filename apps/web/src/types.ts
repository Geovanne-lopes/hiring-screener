export type CriteriosDet = {
  cargos: { ativo: boolean; aceitos: string[]; bloqueados: string[] };
  empresas: { ativo: boolean; bloqueadas: string[] };
  idade: { ativo: boolean; minima: number | null; maxima: number | null };
  escolaridade: {
    ativo: boolean;
    configuracao: { modelo: string; aceitos: string[] };
  };
};

export type Projeto = {
  projetoId: string;
  nome: string;
  criadoEm: string | null;
  atualizadoEm: string | null;
  promptVigenteId: string | null;
  criteriosDeterministicos: CriteriosDet;
  criteriosVersao: string | null;
  criteriosQualitativosVersaoId: string | null;
  mapeamentoColunas: Mapeamento | null;
  quantidadeCandidatos: number;
};

export type Mapeamento = {
  ultimoCargo: string | null;
  idade: string | null;
  escolaridade: string | null;
  empresa: string | null;
  nomeExibicao: string | null;
  respostasChatbot: string[];
  cidade: string | null;
  statusLegado: string | null;
};

export type Motivo = {
  criterio: string;
  codigo: string;
  valorLido: string | null;
  valorComparado: string | null;
  esperado?: unknown;
  mensagem: string;
};

export type Envelope = {
  candidatoId: string;
  linhaOrigem: number;
  nomeExibicao: string | null;
  ultimoCargo: string | null;
  idade: string | null;
  escolaridade: string | null;
  temRespostaUtilizavel: boolean;
  resultadoExibicao: string;
  selecionavel?: boolean;
  incluidoPadrao?: boolean;
  decisao: {
    resultado: string;
    motivos: Motivo[];
    criteriosInativos: string[];
    criteriosVersao: string;
  } | null;
  avaliacao: {
    promptVersionId: string;
    jobDescriptionVersaoId?: string | null;
    perfil: string | null;
    compatibilidade: string | null;
    justificativasPorCriterio: Array<{
      criterioId: string;
      nome: string;
      resultado: string;
      justificativa: string;
      trecho: string;
    }> | null;
    usoToken: { entrada: number | null; saida: number | null; total: number | null } | null;
    estado: string;
    erro: { codigo: string; mensagem: string } | null;
    criadoEm: string | null;
    schema?: "por_pergunta" | "legado";
    porPergunta?: Array<{
      perguntaId: string;
      pergunta: string;
      resultado: string;
      justificativa: string;
      trecho: string;
      rotulo: string;
    }> | null;
    notaTecnica?: number | null;
    notaComportamental?: number | null;
    justificativaNotaTecnica?: string | null;
    justificativaNotaComportamental?: string | null;
  } | null;
  ranking?: {
    notaFinal: number | null;
    notaTecnicaZeradaPorFaltaDeInformacao: boolean;
    posicaoTecnica: number | null;
    posicaoComportamental: number | null;
    posicaoFinal: number | null;
    totalComNota: number;
  };
};

export type ItemQual = {
  criterioId?: string;
  nome: string;
  descricao: string;
  ordem: number;
  eliminatorio: boolean;
};
