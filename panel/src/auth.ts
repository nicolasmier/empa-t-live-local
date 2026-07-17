export interface SesionPanel {
  usuarioId: number;
  rol: "admin" | "operador";
}

// El JWT de sesión de panel va firmado, no cifrado: decodificar su payload en
// cliente es seguro (igual que hace cualquier librería jwt-decode) y evita
// necesitar un endpoint "quién soy" solo para conocer el rol.
export function decodificarSesion(token: string): SesionPanel | null {
  try {
    const payload = token.split(".")[1];
    const json = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    if (json.tipo !== "panel") return null;
    return { usuarioId: Number(json.sub), rol: json.rol };
  } catch {
    return null;
  }
}
