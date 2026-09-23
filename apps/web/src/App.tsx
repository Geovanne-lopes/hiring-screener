import type { ReactNode } from "react";
import { Navigate, Route, Routes, useParams } from "react-router-dom";
import Layout from "./Layout";
import Projetos from "./pages/Projetos";
import Criterios from "./pages/Criterios";
import Importar from "./pages/Importar";
import Triagem from "./pages/Triagem";
import Qualitativos from "./pages/Qualitativos";
import Prompt from "./pages/Prompt";
import Avaliacao from "./pages/Avaliacao";
import Resultado from "./pages/Resultado";

function Guard({ children }: { children: ReactNode }) {
  const { projetoId } = useParams();
  if (!projetoId) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Projetos />} />
        <Route path="/projetos/:projetoId/criterios" element={<Guard><Criterios /></Guard>} />
        <Route path="/projetos/:projetoId/importar" element={<Guard><Importar /></Guard>} />
        <Route path="/projetos/:projetoId/triagem" element={<Guard><Triagem /></Guard>} />
        <Route path="/projetos/:projetoId/qualitativos" element={<Guard><Qualitativos /></Guard>} />
        <Route path="/projetos/:projetoId/prompt" element={<Guard><Prompt /></Guard>} />
        <Route path="/projetos/:projetoId/avaliacao" element={<Guard><Avaliacao /></Guard>} />
        <Route path="/projetos/:projetoId/resultado" element={<Guard><Resultado /></Guard>} />
      </Route>
    </Routes>
  );
}
