INSERT INTO roles (nombre) VALUES ('SuperAdministrador')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO roles (nombre) VALUES ('Usuario_Comun')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO usuarios (nombre, email, password_hash, rol_id)
SELECT 'Super Admin', 'superadmin@example.com', '123456', roles.id
FROM roles
WHERE roles.nombre = 'SuperAdministrador'
ON CONFLICT (email) DO NOTHING;
