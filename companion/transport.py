"""
@doc python-client
@locale en
@title Local Python client API
@section External clients / Python API
@order 100
@symbol companion.transport.Client
Connect a local Python client, read the current runtime and call documented bridge methods.

## Imports and signatures {#api}

```python
from companion.transport import Client, discover, version

# Public call signatures:
# discover()
# Client(pipe)
# Client.call(method, **arguments)
# Client.state(runtime)
# version(state)
```

Use the developer package on Windows with Python 3.11+. Import companion.transport; no external transport library is required. The same local Windows user must run the game and the client.

## Parameters and return values {#parameters}

| Callable | Parameters | Return |
| --- | --- | --- |
| discover | none | List of matching local named-pipe strings; empty on other platforms. |
| Client | pipe: a discovered local CyRSAssistant pipe string | A client bound to that pipe. |
| Client.call | method: documented bridge method; arguments: its named payload fields | The decoded response dictionary, including ok and the method-specific result. |
| Client.state | runtime: selected positive runtime ID | The state dictionary returned by get_state. |
| version | state: a current state dictionary | session, runtime, generation and revision fields for an edit. |

## Read the current state {#example}

```python
from companion.transport import Client, discover

pipes = discover()
if len(pipes) != 1:
    raise RuntimeError("Select one running game explicitly")
client = Client(pipes[0])
sessions = client.call("list_sessions")["runtimes"]
if len(sessions) != 1:
    raise RuntimeError("Select a runtime explicitly")
state = client.state(sessions[0]["runtime"])
print(state["generation"], state["revision"])
```

For an edit, read fresh state and pass **version(state) with the method's remaining fields. See [bridge methods and tokens](doc:protocol#state), [permissions](doc:protocol#permissions) and [MCP clients](doc:mcp).

## Errors and limits {#errors}

An invalid pipe or oversized request raises ValueError. Disconnects can raise ConnectionError or OSError. A bridge response with ok=false raises RuntimeError with its error text. JSON values must be finite. Requests are limited to 1 MiB and responses to 8 MiB. Opening retries certain transient pipe errors for up to three seconds; this is not a whole-operation timeout. After a timeout or uncertain result, read current state before deciding whether to retry an edit.
"""

"""
@doc python-client
@locale fr
@title API du client Python local
@section Clients externes / API Python
@order 100
@symbol companion.transport.Client
Connectez un client Python local, lisez le runtime courant et appelez les méthodes documentées du pont.

## Imports et signatures {#api}

```python
from companion.transport import Client, discover, version

# Signatures des appels publics :
# discover()
# Client(pipe)
# Client.call(method, **arguments)
# Client.state(runtime)
# version(state)
```

Utilisez le paquet développeur sous Windows avec Python 3.11+. Importez companion.transport ; aucune bibliothèque de transport externe n’est nécessaire. Le jeu et le client doivent utiliser le même compte Windows local.

## Paramètres et valeurs de retour {#parameters}

| Appel | Paramètres | Retour |
| --- | --- | --- |
| discover | aucun | Liste des canaux nommés locaux correspondants ; vide sur les autres plateformes. |
| Client | pipe : chaîne d’un canal CyRSAssistant découvert | Client associé à ce canal. |
| Client.call | method : méthode documentée du pont ; arguments : champs nommés de sa requête | Dictionnaire de réponse décodé, avec ok et le résultat propre à la méthode. |
| Client.state | runtime : identifiant positif du runtime choisi | Dictionnaire state renvoyé par get_state. |
| version | state : dictionnaire d’état courant | Champs session, runtime, generation et revision nécessaires à une modification. |

## Lire l’état actuel {#example}

```python
from companion.transport import Client, discover

pipes = discover()
if len(pipes) != 1:
    raise RuntimeError("Choisissez explicitement un jeu ouvert")
client = Client(pipes[0])
sessions = client.call("list_sessions")["runtimes"]
if len(sessions) != 1:
    raise RuntimeError("Choisissez explicitement un runtime")
state = client.state(sessions[0]["runtime"])
print(state["generation"], state["revision"])
```

Pour modifier le rendu, relisez l’état et transmettez **version(state) avec les autres champs de la méthode. Consultez les [méthodes et jetons du pont](doc:protocol#state), les [autorisations](doc:protocol#permissions) et les [clients MCP](doc:mcp).

## Erreurs et limites {#errors}

Un canal invalide ou une requête trop volumineuse lève ValueError. Une déconnexion peut lever ConnectionError ou OSError. Une réponse avec ok=false lève RuntimeError avec son message d’erreur. Les valeurs JSON doivent être finies. Les requêtes sont limitées à 1 Mio et les réponses à 8 Mio. L’ouverture réessaie certaines erreurs temporaires du canal pendant trois secondes au maximum ; ce délai ne couvre pas toute l’opération. Après un délai dépassé ou un résultat incertain, relisez l’état avant de décider de réessayer une modification.
"""

import json
import os
import struct
import time
import uuid


def discover():
    if os.name != "nt":
        return []
    return sorted("\\\\.\\pipe\\" + name for name in os.listdir("\\\\.\\pipe\\") if name.startswith("CyRSAssistant-"))


def read_exact(stream, count):
    result = bytearray()
    while len(result) < count:
        part = stream.read(count - len(result))
        if not part:
            raise ConnectionError("Add-on disconnected")
        result.extend(part)
    return bytes(result)


class Client:
    def __init__(self, pipe):
        if not pipe.startswith("\\\\.\\pipe\\CyRSAssistant-") or not pipe.rsplit("-", 1)[-1].isdigit():
            raise ValueError("Expected a local CyRSAssistant named pipe")
        self.pipe = pipe

    def call(self, method, **arguments):
        body = {"protocol": 1, "request_id": str(uuid.uuid4()), "method": method, **arguments}
        encoded = json.dumps(body, allow_nan=False).encode("utf-8")
        if len(encoded) > 1024 * 1024:
            raise ValueError("Request exceeds 1 MiB")
        deadline = time.monotonic() + 3
        while True:
            try:
                stream = open(self.pipe, "r+b", buffering=0)
                break
            except OSError as exc:
                # CPython's CRT may map a pipe instance closing between calls to
                # EINVAL without winerror. No bytes were sent yet, so opening is safe to retry.
                retryable = getattr(exc, "winerror", None) in (2, 231, 232) or exc.errno == 22 or isinstance(exc, (FileNotFoundError, PermissionError))
                if not retryable or time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)
        with stream:
            data = struct.pack("<I", len(encoded)) + encoded
            while data:
                written = stream.write(data)
                if not written:
                    raise ConnectionError("Failed to send request")
                data = data[written:]
            size, = struct.unpack("<I", read_exact(stream, 4))
            if not 0 < size <= 8 * 1024 * 1024:
                raise ValueError("Invalid response size")
            response_bytes = read_exact(stream, size)
            stream.write(b"\x01")
            result = json.loads(response_bytes)
        if not result.get("ok"):
            raise RuntimeError(result.get("error", "Unknown add-on error"))
        return result

    def state(self, runtime):
        return self.call("get_state", runtime=runtime)["state"]


def version(state):
    return {key: state[key] for key in ("session", "runtime", "generation", "revision")}
