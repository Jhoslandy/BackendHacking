INSERT INTO roles (nombre) VALUES ('Administrador')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO roles (nombre) VALUES ('Usuario_Regular')
ON CONFLICT (nombre) DO NOTHING;
