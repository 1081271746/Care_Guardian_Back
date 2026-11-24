"""HTTP-only seed client. Exceptions never expose credentials or response bodies."""
from urllib.parse import urlsplit
import httpx


class SeedError(RuntimeError):
    pass


def validate_url(url):
    parsed = urlsplit(url)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.scheme not in ({"http", "https"} if local else {"https"})):
        raise SeedError("SEED_BASE_URL debe ser HTTPS sin credenciales, consulta ni fragmento (HTTP solo local)")
    return local


class SeedClient:
    def __init__(self, url, email, password, *, transport=None):
        validate_url(url)
        if not email or not password:
            raise SeedError("Configura SEED_EMAIL y SEED_PASSWORD mediante variables seguras")
        self._email, self._password = email, password
        self._token = None
        self._http = httpx.Client(base_url=url.rstrip("/") + "/", timeout=30,
                                  follow_redirects=False, transport=transport)

    def close(self):
        self._token = None
        self._password = ""
        self._http.close()

    def _send(self, method, path, **kwargs):
        try:
            return self._http.request(method, path.lstrip("/"), **kwargs)
        except httpx.HTTPError:
            raise SeedError("Error de transporte; no se reintentó ninguna escritura. Reejecuta para reconciliar.") from None

    def login(self):
        response = self._send("POST", "/auth/login",
                              json={"email": self._email, "password": self._password})
        if response.status_code != 200:
            raise SeedError(f"No fue posible autenticar: HTTP {response.status_code}")
        data = self._json(response)
        if not isinstance(data, dict) or not isinstance(data.get("access_token"), str) or not data["access_token"]:
            raise SeedError("La autenticación no devolvió un token válido")
        self._token = data["access_token"]

    @staticmethod
    def _json(response):
        try:
            return response.json()
        except ValueError:
            raise SeedError("La API devolvió una respuesta JSON inválida") from None

    def request(self, method, path, payload=None):
        if method not in {"GET", "POST"}:
            raise SeedError("La carga solo permite consultar o crear; nunca modificar ni borrar")
        if self._token is None:
            self.login()
        for attempt in range(2):
            response = self._send(method, path, headers={"Authorization": f"Bearer {self._token}"},
                                  **({"json": payload} if payload is not None else {}))
            if response.status_code == 401 and attempt == 0:
                self.login()
                continue
            if response.status_code not in ({200} if method == "GET" else {200, 201}):
                raise SeedError(f"Operación {method} rechazada: HTTP {response.status_code}")
            return self._json(response)
        raise SeedError("No fue posible renovar la sesión")
