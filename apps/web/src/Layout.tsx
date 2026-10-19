import { NavLink, Outlet, useParams } from "react-router-dom";

const passos = [
  { to: (id: string) => `/projetos/${id}/criterios`, label: "2. Critérios duros" },
  { to: (id: string) => `/projetos/${id}/job-description`, label: "3. Job description" },
  { to: (id: string) => `/projetos/${id}/importar`, label: "4. Importar" },
  { to: (id: string) => `/projetos/${id}/triagem`, label: "5. Triagem" },
  { to: (id: string) => `/projetos/${id}/prompt`, label: "6. Prompt" },
  { to: (id: string) => `/projetos/${id}/avaliacao`, label: "7. Avaliação IA" },
  { to: (id: string) => `/projetos/${id}/resultado`, label: "Resultado" },
];

export default function Layout() {
  const { projetoId } = useParams();
  return (
    <div className="shell">
      <nav className="nav">
        <h1>Screener</h1>
        <NavLink to="/" end>
          1. Projetos
        </NavLink>
        {projetoId ? (
          passos.map((p) => (
            <NavLink key={p.label} to={p.to(projetoId)}>
              {p.label}
            </NavLink>
          ))
        ) : (
          <p className="hint">Abra ou crie um projeto para continuar.</p>
        )}
        <button
          type="button"
          className="nav-btn disabled"
          disabled
          title="Função vem em sprint posterior"
          onClick={(e) => e.preventDefault()}
        >
          Avaliar trajetória
        </button>
        <p className="hint">Função vem em sprint posterior. Não dispara modelo.</p>
      </nav>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
