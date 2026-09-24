"""Overlay approvals for integrated assistant operations; no provider can approve itself."""
import time
from .localization import tr as _, localized

WRITE_METHODS = {"apply_patch", "generate_effect", "replace_game_shader", "enable_game_shader",
                 "restore_game_shaders", "restore_generated_effect", "reload_effects", "undo", "save_preset"}


class PermissionDenied(RuntimeError):
    pass


@localized(2)
def describe(action, payload, state):
    if action == "read_effect_source":
        return _("Read and send the source of {file} to the provider.", file=payload.get("file", ""))
    if action == "inspect_game_shader":
        return _("Read and send the disassembly of shader {hash} to the provider.", hash=payload.get("hash", ""))
    if action == "generate_effect":
        target = payload.get("replace_effect")
        return (_("Replace {file}. The proposed code and controls are shown below.", file=target) if target else
                _("Add effect {name}. The proposed code and controls are shown below.", name=payload.get("title", payload.get("name", "GeneratedEffect"))))
    if action == "apply_patch":
        labels = []
        for change in payload.get("changes", [])[:8]:
            entries = state.get("parameters" if change.get("kind") == "parameter" else "techniques", [])
            item = next((p for p in entries if p["id"] == change.get("id")), {})
            labels.append(str(item.get("effect", "?")) + " / " + str(item.get("name", change.get("id"))) + " = " + str(change.get("value")))
        return _("Apply {count} setting(s): {settings}", count=len(payload.get("changes", [])), settings="; ".join(labels))
    return {"replace_game_shader": _("Compile and replace game shader {hash}.", hash=payload.get("hash", "")),
            "enable_game_shader": _("Change replacement activation for {hash}.", hash=payload.get("hash", "")),
            "restore_game_shaders": _("Restore original game shaders."),
            "restore_generated_effect": _("Restore the replaced ReShade effect."),
            "undo": _("Undo the last edit."), "reload_effects": _("Reload ReShade effects."),
            "save_preset": _("Save settings to the active preset.")}.get(action, action)


class PermissionClient:
    def __init__(self, client, runtime, original, timeout=600):
        self.client, self.runtime, self.original = client, runtime, original
        self.timeout = timeout

    def state(self, runtime):
        return self.client.state(runtime)

    def checked_state(self):
        current = self.state(self.runtime)
        if current["session"] != self.original["session"] or current["prompt"]["id"] != self.original["prompt"]["id"] or not current["prompt"]["pending"]:
            raise PermissionDenied(_("Request cancelled or superseded; no new action is authorized."))
        return current

    def authorize(self, action, payload):
        current = self.checked_state()
        if "generation" in payload and (payload["generation"] != current["generation"] or payload["revision"] != current["revision"]):
            raise ValueError(_("The state changed before approval. Read the values again before proposing this edit."))
        permission = self.client.call("request_action_permission", runtime=self.runtime,
            session=self.original["session"], prompt_id=self.original["prompt"]["id"], action=action,
            payload=payload, summary=describe(action, payload, current).encode("utf-8")[:1900].decode("utf-8", errors="ignore"))["permission"]
        deadline = time.monotonic() + self.timeout
        while permission["status"] == "pending":
            if time.monotonic() >= deadline:
                raise PermissionDenied(_("Approval expired. This action was not executed; send your request again to retry."))
            time.sleep(0.3)
            current = self.checked_state()
            updated = current.get("permissions", {}).get("request")
            if not updated or updated["id"] != permission["id"] or updated["epoch"] != permission["epoch"]:
                raise PermissionDenied(_("Approval cancelled or permission mode changed."))
            permission = updated
        if permission["status"] != "approved":
            raise PermissionDenied(_("Action denied. This action was not executed."))
        return permission["id"]

    def authorize_read(self, action, payload):
        ident = self.authorize(action, payload)
        self.client.call("consume_read_permission", runtime=self.runtime, session=self.original["session"],
                         prompt_id=self.original["prompt"]["id"], permission_id=ident, action=action, payload=payload)

    def call(self, method, **arguments):
        if method in WRITE_METHODS and "prompt_id" in arguments:
            ident = self.authorize(method, arguments)
            return self.client.call(method, **arguments, permission_id=ident)
        if method == "inspect_game_shader":
            self.authorize_read(method, {"hash": arguments["hash"]})
        return self.client.call(method, **arguments)


def with_permissions(client, runtime, state):
    if "permissions" in state and not isinstance(client, PermissionClient):
        return PermissionClient(client, runtime, state)
    return client


def authorize_source(client, filename, offset=0):
    if isinstance(client, PermissionClient):
        client.authorize_read("read_effect_source", {"file": filename, "offset": offset})
