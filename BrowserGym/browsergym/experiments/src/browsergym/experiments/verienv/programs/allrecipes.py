from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any


def _literal_args(call: ast.Call) -> list[Any]:
    args: list[Any] = []
    for a in call.args:
        if isinstance(a, ast.Constant):
            args.append(a.value)
        else:
            # allow strings/numbers only
            raise ValueError("Only literal args are supported in program.check")
    for kw in call.keywords:
        if kw.arg is None or not isinstance(kw.value, ast.Constant):
            raise ValueError("Only literal keyword args are supported in program.check")
        args.append((kw.arg, kw.value.value))
    return args


def _ensure_allrecipes_sdk(clone_coding_root: Path) -> None:
    sdk_root = clone_coding_root / "websites" / "allrecipes" / "python-sdk"
    if str(sdk_root) not in sys.path:
        sys.path.insert(0, str(sdk_root))


def eval_allrecipes_program_check(
    *,
    fn_name: str,
    call: ast.Call,
    clone_coding_root: Path,
    base_url: str,
) -> tuple[bool, dict[str, Any]]:
    """
    Evaluate `judge_for_webagent.program.check` for allrecipes tasks.
    Only supports a curated set of pure verification checks (no state mutation).
    """
    _ensure_allrecipes_sdk(clone_coding_root)
    from allrecipes_sdk import AllrecipesClient  # type: ignore

    try:
        args = _literal_args(call)
    except Exception as e:
        return False, {"error": str(e), "fn": fn_name}

    def _kw_to_dict(args: list[Any]) -> tuple[list[Any], dict[str, Any]]:
        pos: list[Any] = []
        kw: dict[str, Any] = {}
        for a in args:
            if isinstance(a, tuple) and len(a) == 2 and isinstance(a[0], str):
                kw[a[0]] = a[1]
            else:
                pos.append(a)
        return pos, kw

    pos, kw = _kw_to_dict(args)

    try:
        if fn_name == "favorites_contains_slug":
            email, password, slug = pos
            c = AllrecipesClient(base_url)
            c.login(email, password)
            res = c.list_favorites()
            ok = any(x.get("slug") == slug for x in res["data"]["favorites"])
            return ok, {"favorites": [x.get("slug") for x in res["data"]["favorites"]]}

        if fn_name == "favorites_not_contains_slug":
            email, password, slug = pos
            c = AllrecipesClient(base_url)
            c.login(email, password)
            res = c.list_favorites()
            ok = all(x.get("slug") != slug for x in res["data"]["favorites"])
            return ok, {"favorites": [x.get("slug") for x in res["data"]["favorites"]]}

        if fn_name == "review_exists_on_recipe_page":
            recipe_slug = kw.get("recipe_slug")
            user_name = kw.get("user_name")
            title = kw.get("title")
            if not (recipe_slug and user_name and title):
                return False, {"error": "Missing required kwargs", "kwargs": kw}
            c = AllrecipesClient(base_url)
            res = c.get_recipe(recipe_slug)
            reviews = (res.get("data") or {}).get("recipe", {}).get("reviews", [])
            ok = any(
                (rv.get("title") == title and ((rv.get("user") or {}).get("name") == user_name))
                for rv in reviews
            )
            return ok, {"review_count": len(reviews)}

        if fn_name == "favorites_requires_auth":
            c = AllrecipesClient(base_url)
            try:
                c.list_favorites()
                return False, {"error": "Expected Unauthorized, got success"}
            except Exception as e:
                return ("401" in str(e) or "Unauthorized" in str(e)), {"caught": str(e)}

        if fn_name == "favorite_requires_auth":
            c = AllrecipesClient(base_url)
            try:
                c.favorite("chicken-milanese-260")
                return False, {"error": "Expected Unauthorized, got success"}
            except Exception as e:
                return ("401" in str(e) or "Unauthorized" in str(e)), {"caught": str(e)}

        if fn_name == "review_requires_auth":
            c = AllrecipesClient(base_url)
            try:
                c.create_review("chicken-milanese-260", rating=5, title="Test", body="Test")
                return False, {"error": "Expected Unauthorized, got success"}
            except Exception as e:
                return ("401" in str(e) or "Unauthorized" in str(e)), {"caught": str(e)}

        if fn_name == "login_rejects_invalid_password":
            c = AllrecipesClient(base_url)
            try:
                c.login("qa.fav.8cddc26467@example.com", "wrong-password")
                return False, {"error": "Expected login failure, got success"}
            except Exception as e:
                return ("401" in str(e) or "Invalid" in str(e)), {"caught": str(e)}

        return False, {"error": f"Unsupported program check function: {fn_name}"}

    except Exception as e:
        return False, {"error": f"{type(e).__name__}: {e}", "fn": fn_name}


