CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rol
        FOREIGN KEY (rol_id)
        REFERENCES roles(id)
        ON DELETE RESTRICT
);

CREATE TABLE proyectos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    creador_id INT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_proyecto_creador
        FOREIGN KEY (creador_id)
        REFERENCES usuarios(id)
        ON DELETE SET NULL
);

CREATE TABLE proyecto_miembros (
    proyecto_id INT NOT NULL,
    usuario_id INT NOT NULL,
    subrol VARCHAR(50) NOT NULL,
    agregado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (proyecto_id, usuario_id),
    CONSTRAINT chk_proyecto_miembros_subrol
        CHECK (subrol IN ('administrador_proyecto', 'miembro')),
    CONSTRAINT fk_proyecto_miembro_proyecto
        FOREIGN KEY (proyecto_id)
        REFERENCES proyectos(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_proyecto_miembro_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
);

CREATE TABLE tableros (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    proyecto_id INT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tablero_proyecto
        FOREIGN KEY (proyecto_id)
        REFERENCES proyectos(id)
        ON DELETE CASCADE
);

CREATE TABLE columnas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    tablero_id INT NOT NULL,
    orden INT DEFAULT 0,
    CONSTRAINT chk_columnas_nombre
        CHECK (nombre IN ('SOLICITADO', 'EN PROGRESO', 'EN REVISION', 'COMPLETADO')),
    CONSTRAINT uq_columnas_tablero_nombre
        UNIQUE (tablero_id, nombre),
    CONSTRAINT fk_tablero
        FOREIGN KEY (tablero_id)
        REFERENCES tableros(id)
        ON DELETE CASCADE
);

CREATE TABLE tareas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    fecha_vencimiento TIMESTAMP,
    columna_id INT NOT NULL,
    creador_id INT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_columna
        FOREIGN KEY (columna_id)
        REFERENCES columnas(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_creador
        FOREIGN KEY (creador_id)
        REFERENCES usuarios(id)
        ON DELETE SET NULL
);

CREATE TABLE usuario_tarea (
    usuario_id INT NOT NULL,
    tarea_id INT NOT NULL,
    asignado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, tarea_id),
    CONSTRAINT fk_usuario_asignado
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_tarea_asignada
        FOREIGN KEY (tarea_id)
        REFERENCES tareas(id)
        ON DELETE CASCADE
);
