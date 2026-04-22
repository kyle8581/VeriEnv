from __future__ import annotations

import ast
import difflib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Union


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


@dataclass(frozen=True)
class JudgeResult:
    passed: bool
    passed_checks: list[str]
    failed_checks: list[str]
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class JudgeSpec:
    eval_type: str  # rinfo or rprog
    checks: tuple[Union[str, dict], ...]  # Can be string or dict
    parse_mode: str | None = None  # "json" or None
    program_check: str | None = None
    check_logic: str = "AND"  # "AND" or "OR"

    def expected_answer_keys(self) -> set[str]:
        keys: set[str] = set()
        for c in self.checks:
            if isinstance(c, str):
                for m in re.finditer(r"\^a_([a-zA-Z0-9_]+)", c.replace("ˆ", "^")):
                    keys.add(m.group(1))
            elif isinstance(c, dict):
                # For dict checks, path is the key
                path = c.get("path")
                if path:
                    keys.add(path)
        return keys

    def to_dict(self) -> dict[str, Any]:
        return {
            "eval_type": self.eval_type,
            "checks": list(self.checks),
            "parse_mode": self.parse_mode,
            "program_check": self.program_check,
            "check_logic": self.check_logic,
        }


def parse_judge_spec(raw: Any) -> JudgeSpec:
    """
    Supports:
    - dict form: {"eval_type": "rinfo", "checks": [...] } or {"type": "rinfo", ...}
    - dict checks: {"op": "exact_match", "path": "city", "expected": "NYC"} or with "fn"/"value"
    - allrecipes rprog: {"eval_type":"rprog","program":{"check":"fn(...)"}}
    - string form used by babycenter: "rprog: ...; rinfo: ..."
    - parse mode: {"parse": "json", ...} to parse answer as JSON
    """
    if isinstance(raw, dict):
        eval_type = raw.get("eval_type") or raw.get("type") or "rinfo"
        parse_mode = raw.get("parse")  # "json" or None
        check_logic = raw.get("check_logic", "AND")  # "AND" or "OR"
        raw_checks = raw.get("checks") or []
        if not isinstance(raw_checks, list):
            raw_checks = []
        
        # Preserve dict checks as-is, convert strings
        checks: list[Union[str, dict]] = []
        for c in raw_checks:
            if isinstance(c, dict):
                checks.append(c)  # Keep dict format
            else:
                checks.append(str(c))
        
        program_check = None
        if eval_type == "rprog":
            program = raw.get("program")
            if isinstance(program, dict) and isinstance(program.get("check"), str):
                program_check = program["check"]
        return JudgeSpec(
            eval_type=str(eval_type),
            checks=tuple(checks),
            parse_mode=parse_mode,
            program_check=program_check,
            check_logic=check_logic,
        )

    if isinstance(raw, str):
        checks: list[str] = []
        eval_type = "rinfo"
        program_check = None

        # Split by ';' segments: "rprog: ...; rinfo: ..."
        segments = [seg.strip() for seg in raw.split(";") if seg.strip()]
        for seg in segments:
            if ":" not in seg:
                continue
            prefix, body = seg.split(":", 1)
            prefix = prefix.strip()
            body = body.strip()
            # We keep rinfo checks only; rprog parts in string judge are mostly url checks,
            # which can be expressed as must_include(url, ...) and treated like rinfo checks.
            if prefix in {"rinfo", "rprog"}:
                eval_type = eval_type if eval_type == "rprog" else prefix  # prefer rprog if any
                parts = [p.strip() for p in body.split(",") if p.strip()]
                for p in parts:
                    # ignore assignments like url=locate_current_url(s) (we supply url in ctx)
                    if "=" in p and p.split("=", 1)[0].strip().isidentifier():
                        continue
                    checks.append(p)
        return JudgeSpec(eval_type=eval_type, checks=tuple(checks), program_check=program_check)

    return JudgeSpec(eval_type="rinfo", checks=(), program_check=None)


def _value_from_ref(ref: str, *, answer_text: str, answer_obj: Any) -> Any:
    ref = ref.replace("ˆ", "^")
    if ref in {"answer", "response"}:
        return answer_obj if answer_obj is not None else answer_text
    if ref == "^a":
        return answer_obj if answer_obj is not None else answer_text
    if ref.startswith("^a_"):
        key = ref[len("^a_") :]
        if isinstance(answer_obj, dict):
            return answer_obj.get(key)
        return None
    # variable references like url
    return None


def _strip_wrapping_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2:
        pairs = {('"', '"'), ("'", "'"), ("`", "`")}
        if (s[0], s[-1]) in pairs:
            return s[1:-1].strip()
    return s


def _coerce_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return _strip_wrapping_quotes(x)
    return _strip_wrapping_quotes(str(x))


def _coerce_list(x: Any) -> list[Any]:
    if isinstance(x, list):
        return x
    return [x]


def _parse_literal(s: str) -> Any:
    # best-effort parse of python literals found in checks
    try:
        return ast.literal_eval(s)
    except Exception:
        return s.strip().strip('"').strip("'")


def exact_match(target: Any, expected: Any) -> bool:
    """Case-insensitive exact match after normalization."""
    # list comparison
    if isinstance(expected, list):
        t = target
        if isinstance(t, str):
            # allow stringified lists
            try:
                t = ast.literal_eval(t)
            except Exception:
                pass
        # For list comparison, compare lowercase versions
        if isinstance(t, list) and isinstance(expected, list):
            return [str(x).lower().strip() for x in t] == [str(x).lower().strip() for x in expected]
        return t == expected
    return _norm(_coerce_str(target)).lower() == _norm(_coerce_str(expected)).lower()


def must_include(target: Any, needle: Any) -> bool:
    """Case-insensitive substring check."""
    return _coerce_str(needle).lower() in _coerce_str(target).lower()


def fuzzy_match(target: Any, expected: Any, threshold: float = 0.78) -> bool:
    """Case-insensitive fuzzy match."""
    a = _norm(_coerce_str(target))
    b = _norm(_coerce_str(expected))
    if not a and not b:
        return True
    return difflib.SequenceMatcher(a=a.lower(), b=b.lower()).ratio() >= threshold


def must_include_all(target: Any, needles: Iterable[Any]) -> bool:
    """Case-insensitive check that all needles are present."""
    t = _coerce_str(target).lower()
    return all(_coerce_str(n).lower() in t for n in needles)


_FUNC_MAP = {
    "exact_match": exact_match,
    "must_include": must_include,
    "fuzzy_match": fuzzy_match,
    "must_include_all": must_include_all,
}


def _extract_by_path(obj: Any, path: str) -> Any:
    """Extract a value from an object using a dot-separated path."""
    if obj is None:
        return None
    if not path:
        return obj
    
    parts = path.split(".")
    current = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if 0 <= idx < len(current) else None
        else:
            return None
    return current


def _eval_dict_check(
    check: dict,
    *,
    answer_text: str,
    answer_obj: Any,
    ctx: dict[str, Any],
) -> tuple[bool, str]:
    """
    Evaluate a dict-format check.
    Supports:
    - {"op": "exact_match", "path": "city", "expected": "NYC"}
    - {"fn": "exact_match", "path": "city", "value": "NYC"}  (legacy)
    - {"op": "must_include", "expected": "keyword"}  (no path = use full answer)
    """
    # Get operation: prefer "op" over "fn"
    op = check.get("op") or check.get("fn")
    if not op:
        return False, f"Missing 'op' in check: {check}"
    
    if op not in _FUNC_MAP:
        return False, f"Unsupported operation: {op}"
    
    # Get expected value: prefer "expected" over "value"
    expected = check.get("expected")
    if expected is None:
        expected = check.get("value")
    if expected is None:
        return False, f"Missing 'expected' or 'value' in check: {check}"
    
    # Get target value
    path = check.get("path")
    ref = check.get("ref")  # Support ^a style refs
    
    if path:
        # Extract from answer_obj using path
        target = _extract_by_path(answer_obj, path)
    elif ref:
        # Use ^a style reference
        target = _value_from_ref(ref, answer_text=answer_text, answer_obj=answer_obj)
    else:
        # No path/ref = use full answer
        target = answer_obj if answer_obj is not None else answer_text
    
    # Run the check
    ok = _FUNC_MAP[op](target, expected)
    check_desc = f"{op}({path or 'answer'}, {expected!r})"
    return ok, check_desc


def _eval_string_check(
    check_str: str,
    *,
    answer_text: str,
    answer_obj: Any,
    ctx: dict[str, Any],
) -> tuple[bool, str, str | None]:
    """
    Evaluate a string-format check like 'exact_match(^a, "value")'.
    Returns (passed, check_str, error_reason).
    """
    c = check_str.strip()
    if not c:
        return True, c, None
    c_norm = c.replace("ˆ", "^")

    # Parse call like exact_match(^a, "x") or must_include(url, "/pregnancy")
    m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$", c_norm)
    if not m:
        return False, c, f"Unsupported check syntax: {c}"

    fn = m.group(1)
    args_str = m.group(2)
    if fn not in _FUNC_MAP:
        return False, c, f"Unsupported check function: {fn}"

    # naive split on commas at top-level (works for our current checks)
    parts = [p.strip() for p in re.split(r",(?![^\[]*\])", args_str) if p.strip()]
    if len(parts) < 2:
        return False, c, f"Not enough args for {fn}: {c}"

    ref = parts[0]
    # reference can be ^a, ^a_count, url
    target: Any
    ref_norm = ref.replace("ˆ", "^")
    if ref_norm.startswith("^a"):
        target = _value_from_ref(ref, answer_text=answer_text, answer_obj=answer_obj)
    elif ref_norm in {"answer", "response"}:
        target = answer_obj if answer_obj is not None else answer_text
    else:
        target = ctx.get(ref)

    expected = _parse_literal(",".join(parts[1:])) if len(parts) > 2 else _parse_literal(parts[1])

    ok = _FUNC_MAP[fn](target, expected)
    return ok, c, None


def eval_rinfo_checks(
    checks: tuple[Union[str, dict], ...] | list,
    *,
    answer_text: str,
    answer_obj: Any,
    ctx: dict[str, Any] | None = None,
    parse_mode: str | None = None,
    check_logic: str = "AND",  # "AND" or "OR"
) -> JudgeResult:
    ctx = ctx or {}
    passed: list[str] = []
    failed: list[str] = []
    
    # If parse_mode is "json", try to parse answer_text as JSON
    if parse_mode == "json" and answer_obj is None:
        try:
            answer_obj = json.loads(answer_text)
        except (json.JSONDecodeError, TypeError):
            # Try to extract JSON from text (agent might include extra text)
            json_match = re.search(r'\{[^{}]*\}', answer_text)
            if json_match:
                try:
                    answer_obj = json.loads(json_match.group())
                except (json.JSONDecodeError, TypeError):
                    pass

    # OR logic: pass if ANY check passes
    if check_logic.upper() == "OR":
        for raw in checks:
            if isinstance(raw, dict):
                ok, check_desc = _eval_dict_check(
                    raw,
                    answer_text=answer_text,
                    answer_obj=answer_obj,
                    ctx=ctx,
                )
                if ok:
                    passed.append(check_desc)
                    return JudgeResult(True, passed, failed, None)
                else:
                    failed.append(check_desc)
            else:
                ok, c, error = _eval_string_check(
                    str(raw),
                    answer_text=answer_text,
                    answer_obj=answer_obj,
                    ctx=ctx,
                )
                if ok:
                    passed.append(c)
                    return JudgeResult(True, passed, failed, None)
                else:
                    failed.append(c)
        # None passed
        return JudgeResult(False, passed, failed, "No check passed (OR logic)")

    # AND logic (default): all checks must pass
    for raw in checks:
        if isinstance(raw, dict):
            # Dict-format check
            ok, check_desc = _eval_dict_check(
                raw,
                answer_text=answer_text,
                answer_obj=answer_obj,
                ctx=ctx,
            )
            if ok:
                passed.append(check_desc)
            else:
                failed.append(check_desc)
                return JudgeResult(False, passed, failed, f"Check failed: {check_desc}")
        else:
            # String-format check
            ok, c, error = _eval_string_check(
                str(raw),
                answer_text=answer_text,
                answer_obj=answer_obj,
                ctx=ctx,
            )
            if error:
                failed.append(c)
                return JudgeResult(False, passed, failed, error)
            if ok:
                passed.append(c)
            else:
                failed.append(c)
                return JudgeResult(False, passed, failed, f"Check failed: {c}")

    return JudgeResult(True, passed, failed, None)


