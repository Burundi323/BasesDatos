import { useState } from "react";
import "./App.css";

const CONSULTAS = [
  {
    id: 1,
    titulo: "Prerrequisitos de un curso",
    descripcion:
      "Encontrar los prerrequisitos de un curso. El curso se introduce en la pregunta. Si se introduce un curso inexistente la aplicación debe enviar un mensaje de que ese curso no existe.",
    campos: [
      {
        name: "courseId",
        label: "ID del curso",
        placeholder: "Ejemplo: 376",
      },
    ],
  },
  {
    id: 2,
    titulo: "Historial académico de un estudiante",
    descripcion:
      "Obtener el historial académico completo (transcript) de un estudiante. El ID del estudiante se especifica en la pregunta.",
    campos: [
      {
        name: "studentId",
        label: "ID del estudiante",
        placeholder: "Ejemplo: 24746",
      },
    ],
  },
  {
    id: 3,
    titulo: "Detalles de una sección",
    descripcion:
      "Encontrar los detalles (horario y aula) de una sección específica. Se pide el ID de la sección.",
    campos: [
      {
        name: "sectionId",
        label: "ID de la sección",
        placeholder: "Ejemplo: 1",
      },
    ],
  },
  {
    id: 4,
    titulo: "Secciones de un edificio",
    descripcion:
      "Encontrar todas las secciones que se imparten en el edificio X.",
    campos: [
      {
        name: "building",
        label: "Nombre del edificio",
        placeholder: "Ejemplo: Gates",
      },
    ],
  },
  {
    id: 5,
    titulo: "Estudiante y su asesor",
    descripcion:
      "Encontrar el nombre de un estudiante X y el nombre de su asesor.",
    campos: [
      {
        name: "studentName",
        label: "Nombre del estudiante",
        placeholder: "Ejemplo: Schrefl",
      },
    ],
  },
  {
    id: 6,
    titulo: "Estudiantes con 'A' en un curso",
    descripcion:
      "Encontrar a todos los estudiantes que obtuvieron una 'A' en el curso X.",
    campos: [
      {
        name: "courseName",
        label: "Nombre o ID del curso",
        placeholder: "Ejemplo: 401",
      },
    ],
  },
  {
    id: 7,
    titulo: "Estudiantes asesorados por un profesor",
    descripcion:
      "Encontrar los nombres de todos los estudiantes asesorados por el profesor de nombre X.",
    campos: [
      {
        name: "professorName",
        label: "Nombre del profesor",
        placeholder: "Ejemplo: McKinnon",
      },
    ],
  },
  {
    id: 8,
    titulo: "Cursos impartidos por un profesor",
    descripcion:
      "Encontrar todos los cursos (título, horario y aula) que imparte el profesor de nombre X.",
    campos: [
      {
        name: "professorName",
        label: "Nombre del profesor",
        placeholder: "Ejemplo: McKinnon",
      },
    ],
  },
  {
    id: 9,
    titulo: "Salario promedio por departamento",
    descripcion: "Calcular el salario promedio por departamento.",
    campos: [],
  },
  {
    id: 10,
    titulo: "Estudiantes del depto. X con > 90 créditos",
    descripcion:
      "Encontrar todos los estudiantes del departamento X con más de 90 créditos.",
    campos: [
      {
        name: "departmentName",
        label: "Nombre del departamento",
        placeholder: "Ejemplo: History",
      },
    ],
  },
];

function App() {
  // Login
  const [loggedIn, setLoggedIn] = useState(false);
  const [loginValues, setLoginValues] = useState({
    username: "",
    password: "",
  });

  // Base de datos seleccionada
  const [selectedDB, setSelectedDB] = useState("mongo"); // "mongo" o "mysql"

  // Consultas
  const [selectedId, setSelectedId] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [exited, setExited] = useState(false);

  const pageSize = 10;
  const selectedConsulta = CONSULTAS.find((c) => c.id === selectedId);

  // --- Login ---
  const handleLoginChange = (field, value) => {
    setLoginValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    setLoggedIn(true);
    setSelectedId(null);
    setExited(false);
  };

  // --- Botón SALIR ---
  const handleExit = () => {
    setExited(true);
    setSelectedId(null);
    setResult(null);
    setError("");
    setFormValues({});
    setPage(1);
  };

  // --- Menú de consultas ---
  const handleBubbleClick = (id) => {
    setExited(false);
    setSelectedId(id);
    setFormValues({});
    setResult(null);
    setError("");
    setPage(1);
  };

  // --- Cambiar base de datos ---
  const handleDBChange = (db) => {
    setSelectedDB(db);
    setResult(null);
    setError("");
  };

  // --- Formulario de consulta ---
  const handleInputChange = (name, value) => {
    setFormValues((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!selectedConsulta) return;

    // Validar campos requeridos
    for (const campo of selectedConsulta.campos) {
      const valor = formValues[campo.name];
      if (!valor || valor.trim() === "") {
        setError(`Falta llenar el campo "${campo.label}".`);
        return;
      }
    }

    setError("");
    setLoading(true);
    setResult(null);
    setPage(1);

    try {
      const data = await ejecutarConsulta(selectedConsulta.id, formValues, selectedDB);
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Ocurrió un error al ejecutar la consulta.");
    } finally {
      setLoading(false);
    }
  };

  // --- Paginación ---
  const rows = result?.rows ?? [];
  const columns = result?.columns ?? [];
  const totalPages = rows.length > 0 ? Math.ceil(rows.length / pageSize) : 1;
  const startIndex = (page - 1) * pageSize;
  const visibleRows = rows.slice(startIndex, startIndex + pageSize);

  const handlePrevPage = () => setPage((p) => Math.max(1, p - 1));
  const handleNextPage = () => setPage((p) => Math.min(totalPages, p + 1));

  // --- Render ---
  if (!loggedIn) {
    return (
      <div className="app">
        <header className="topbar">
          <h1>Portal de Consultas</h1>
        </header>

        <main className="main login-main">
          <div className="login-card">
            <h2>Iniciar sesión</h2>
            <p className="login-subtitle">
              Ingresa cualquier usuario y contraseña para continuar.
            </p>
            <form onSubmit={handleLoginSubmit} className="login-form">
              <div className="form-group">
                <label htmlFor="username">Usuario</label>
                <input
                  id="username"
                  type="text"
                  value={loginValues.username}
                  onChange={(e) => handleLoginChange("username", e.target.value)}
                  placeholder="usuario"
                />
              </div>
              <div className="form-group">
                <label htmlFor="password">Contraseña</label>
                <input
                  id="password"
                  type="password"
                  value={loginValues.password}
                  onChange={(e) => handleLoginChange("password", e.target.value)}
                  placeholder="••••••••"
                />
              </div>
              <button type="submit" className="btn-primary login-btn">
                Entrar
              </button>
            </form>
          </div>
        </main>

        <footer className="footer">
          <small>Proyecto Introducción a Bases de Datos</small>
        </footer>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Consultas a la base de datos</h1>
        <div className="topbar-right">
          {/* Selector de base de datos */}
          <div className="db-selector">
            <button
              className={`db-btn ${selectedDB === "mongo" ? "active" : ""}`}
              onClick={() => handleDBChange("mongo")}
            >
               MongoDB
            </button>
            <button
              className={`db-btn ${selectedDB === "mysql" ? "active" : ""}`}
              onClick={() => handleDBChange("mysql")}
            >
               MySQL
            </button>
          </div>
          <button className="btn-exit-top" onClick={handleExit}>
            SALIR
          </button>
        </div>
      </header>

      <main className="main">
        {exited ? (
          <div className="exit-message fade-in">
            <h2>Aplicación finalizada</h2>
            <p>
              Se seleccionó la opción de salir. Puedes cerrar esta pestaña o
              recargar la página para iniciar de nuevo.
            </p>
          </div>
        ) : (
          <div className="consulta-page">
            {/* Indicador de base de datos actual */}
            <div className="db-indicator">
              Base de datos actual:{" "}
              <span className={`db-tag ${selectedDB}`}>
                {selectedDB === "mongo" ? "🍃 MongoDB Atlas" : "🐬 MySQL Local"}
              </span>
            </div>

            {/* Burbujas horizontales con scroll */}
            <div className="consulta-strip">
              {CONSULTAS.map((consulta) => (
                <button
                  key={consulta.id}
                  className={
                    consulta.id === selectedId
                      ? "consulta-bubble active"
                      : "consulta-bubble"
                  }
                  onClick={() => handleBubbleClick(consulta.id)}
                >
                  <span className="consulta-badge">{consulta.id}</span>
                  <span className="consulta-title">{consulta.titulo}</span>
                </button>
              ))}
            </div>

            {/* Contenido de la consulta seleccionada */}
            <section className="content consulta-panel slide-up">
              {selectedConsulta ? (
                <>
                  <h2>{selectedConsulta.titulo}</h2>
                  <p className="descripcion">{selectedConsulta.descripcion}</p>

                  <form className="form" onSubmit={handleSubmit}>
                    {selectedConsulta.campos.map((campo) => (
                      <div className="form-group" key={campo.name}>
                        <label htmlFor={campo.name}>{campo.label}</label>
                        <input
                          id={campo.name}
                          type="text"
                          value={formValues[campo.name] || ""}
                          placeholder={campo.placeholder}
                          onChange={(e) =>
                            handleInputChange(campo.name, e.target.value)
                          }
                        />
                      </div>
                    ))}

                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={loading}
                    >
                      {loading ? "Consultando..." : "Ejecutar consulta"}
                    </button>
                  </form>

                  {error && <p className="error">{error}</p>}

                  {result && (
                    <div className="resultado fade-in">
                      <h3>Resultado</h3>

                      {rows.length === 0 ? (
                        <p>No se encontraron datos para los criterios dados.</p>
                      ) : (
                        <>
                          <div className="tabla-contenedor">
                            <table className="tabla">
                              <thead>
                                <tr>
                                  {columns.map((col) => (
                                    <th key={col}>{col}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {visibleRows.map((row, index) => (
                                  <tr key={index}>
                                    {row.map((cell, i) => (
                                      <td key={i}>{cell}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>

                          {rows.length > pageSize && (
                            <div className="paginacion">
                              <button
                                type="button"
                                onClick={handlePrevPage}
                                disabled={page === 1}
                              >
                                Anterior
                              </button>
                              <span>
                                Página {page} de {totalPages} — mostrando{" "}
                                {startIndex + 1}-
                                {Math.min(startIndex + pageSize, rows.length)}{" "}
                                de {rows.length} filas
                              </span>
                              <button
                                type="button"
                                onClick={handleNextPage}
                                disabled={page === totalPages}
                              >
                                Siguiente
                              </button>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <p className="placeholder">
                  Selecciona una consulta en las burbujas de arriba.
                </p>
              )}
            </section>
          </div>
        )}
      </main>

      <footer className="footer">
        <small>Proyecto Introducción a Bases de Datos</small>
      </footer>
    </div>
  );
}

/**
 * Llama a la API seleccionada (MongoDB o MySQL)
 */
async function ejecutarConsulta(id, params, database) {
  const BASE_URL = "http://localhost:8000";
  
  // Cambiar el endpoint según la base de datos seleccionada
  const dbPath = database === "mongo" ? "mongo" : "mysql";
  const url = `${BASE_URL}/api/${dbPath}/consulta/${id}`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(
      `Error HTTP ${response.status} ${response.statusText} ${text}`
    );
  }

  const data = await response.json();

  if (!data.columns || !data.rows) {
    throw new Error("La respuesta de la API no tiene 'columns' o 'rows'.");
  }

  return data;
}

export default App;
