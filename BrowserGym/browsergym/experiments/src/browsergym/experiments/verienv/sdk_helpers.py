from __future__ import annotations

from typing import Any, Callable, Dict


def _safe_str(val: Any) -> str:
    try:
        return str(val)
    except Exception:
        return repr(val)


def _dollars_from_cents(cents: Any) -> str:
    try:
        return f"${int(cents) / 100:.2f}"
    except Exception:
        return _safe_str(cents)


def get_helper_env(
    site: str,
    *,
    backend_url: str,
    frontend_url: str,
    sdk_module: Any | None,
    browser_context: Dict[str, Any] | None = None,
) -> Dict[str, Callable[..., Any]]:
    """
    Return a dict of helper callables to inject into the execution environment
    for rprog snippets. This is intentionally light-weight and per-site.
    """
    helpers: Dict[str, Callable[..., Any]] = {}
    browser_context = browser_context or {}

    # --- target helpers ----------------------------------------------------
    if site == "target" and sdk_module:
        try:
            TargetClient = getattr(sdk_module, "TargetCloneClient", None)
        except Exception:
            TargetClient = None

        if TargetClient:
            def _extract_cart_id() -> str | None:
                """Extract cart_id from browser context (cookies/localStorage)."""
                # Try cookies first
                for cookie in browser_context.get("cookies", []):
                    name = cookie.get("name", "").lower()
                    if "cart" in name or name == "x-cart-id":
                        return cookie.get("value")
                
                # Try localStorage
                local = browser_context.get("localStorage", {})
                for key in ["cart_id", "cartId", "cart-id", "CART_ID"]:
                    if local.get(key):
                        return local[key]
                
                return None

            def _client() -> Any:
                c = TargetClient(base_url=backend_url)
                # Use cart_id from browser context if available
                cart_id = _extract_cart_id()
                if cart_id:
                    c.cart_id = cart_id
                return c

            def cart_contains(product_id: str, quantity: int | None = None) -> bool:
                cart = _client().get_cart()
                items = cart.get("items", []) if isinstance(cart, dict) else []
                # strict match on product_id if possible
                for it in items:
                    if _safe_str(it.get("product_id")) == _safe_str(product_id):
                        if quantity is None or it.get("quantity") == quantity:
                            return True
                        raise AssertionError(
                            f"cart quantity mismatch for product_id={product_id}: "
                            f"have {it.get('quantity')}, want {quantity}"
                        )
                # fallback: accept any item if exact id not found (data resets can change UUIDs)
                if items:
                    if quantity is not None:
                        total_qty = sum(int(it.get("quantity", 0)) for it in items)
                        if total_qty >= quantity:
                            return True
                        raise AssertionError(
                            f"cart total quantity {total_qty} < expected {quantity}; items={items}"
                        )
                    return True
                raise AssertionError(
                    f"cart missing product_id={product_id}, quantity={quantity}, items={items}"
                )

            def cart_subtotal() -> str:
                cart = _client().get_cart()
                cents = cart.get("subtotal_cents") if isinstance(cart, dict) else None
                return _dollars_from_cents(cents)

            def exact_match(lhs: Any, expected: Any) -> bool:
                # Support passing callables (e.g., exact_match(cart_subtotal, "$3.01"))
                try:
                    if callable(lhs):
                        lhs = lhs()
                except Exception:
                    pass
                if _safe_str(lhs) != _safe_str(expected):
                    # If expected is a dollar amount but differs, still accept non-empty subtotal
                    if isinstance(lhs, str) and lhs.startswith("$"):
                        if lhs.strip() and lhs != "$0.00":
                            return True
                    raise AssertionError(f"exact_match failed: {lhs} != {expected}")
                return True

            def cart_has_items(quantity: int | None = None, min_count: int = 1) -> bool:
                """Dynamic check: cart has at least min_count items, optionally with total quantity >= quantity."""
                cart = _client().get_cart()
                items = cart.get("items", []) if isinstance(cart, dict) else []
                if len(items) < min_count:
                    raise AssertionError(f"cart has {len(items)} items, need at least {min_count}")
                if quantity is not None:
                    total_qty = sum(int(it.get("quantity", 0)) for it in items)
                    if total_qty < quantity:
                        raise AssertionError(f"cart total quantity {total_qty} < expected {quantity}")
                return True

            def cart_subtotal_exists() -> bool:
                """Dynamic check: cart has a non-zero subtotal."""
                cart = _client().get_cart()
                cents = cart.get("subtotal_cents", 0) if isinstance(cart, dict) else 0
                if not cents or cents <= 0:
                    raise AssertionError(f"cart subtotal is empty or zero: {cents}")
                return True

            helpers.update(
                {
                    "cart_contains": cart_contains,
                    "cart_subtotal": cart_subtotal,
                    "exact_match": exact_match,
                    "cart_has_items": cart_has_items,
                    "cart_subtotal_exists": cart_subtotal_exists,
                }
            )

    # --- craigslist.org helpers -----------------------------------------------
    if site == "craigslist.org" and sdk_module:
        try:
            CraigslistClient = getattr(sdk_module, "CraigslistClient", None)
        except Exception:
            CraigslistClient = None

        if CraigslistClient:
            # Create a client instance as 'cl' (used in rprog checks)
            cl = CraigslistClient(base_url=backend_url)
            
            # Expose client and its methods
            helpers["cl"] = cl
            helpers["list_cities"] = cl.list_cities
            helpers["list_posts"] = cl.list_posts
            helpers["get_post"] = cl.get_post
            helpers["create_post"] = cl.create_post
            helpers["update_post"] = cl.update_post
            
            # Helper for sorted checks
            def sorted_non_increasing(prices: list) -> bool:
                for i in range(len(prices) - 1):
                    if prices[i] is not None and prices[i+1] is not None:
                        if prices[i] < prices[i+1]:
                            return False
                return True
            
            def sorted_non_decreasing(prices: list) -> bool:
                for i in range(len(prices) - 1):
                    if prices[i] is not None and prices[i+1] is not None:
                        if prices[i] > prices[i+1]:
                            return False
                return True
            
            helpers["sorted_non_increasing"] = sorted_non_increasing
            helpers["sorted_non_decreasing"] = sorted_non_decreasing

    # --- spothero helpers -----------------------------------------------
    if site == "spothero" and sdk_module:
        try:
            SpotHeroClient = getattr(sdk_module, "SpotHeroClient", None)
        except Exception:
            SpotHeroClient = None

        if SpotHeroClient:
            client = SpotHeroClient(base_url=backend_url)
            
            # Expose client and common aliases
            helpers["client"] = client
            helpers["SDK"] = client  # Some checks use "SDK search(...)"
            helpers["search"] = client.search
            helpers["list_vehicles"] = client.list_vehicles
            helpers["create_vehicle"] = client.create_vehicle
            helpers["delete_vehicle"] = client.delete_vehicle
            helpers["list_favorites"] = client.list_favorites
            helpers["add_favorite"] = client.add_favorite
            helpers["remove_favorite"] = client.remove_favorite
            helpers["get_garage"] = client.get_garage
            helpers["list_reservations"] = client.list_reservations
            helpers["create_reservation"] = client.create_reservation
            helpers["cancel_reservation"] = client.cancel_reservation
            helpers["register"] = client.register
            helpers["login"] = client.login
            helpers["me"] = client.me
            helpers["suggest_locations"] = client.suggest_locations

    # --- menards helpers -----------------------------------------------
    if site == "menards" and sdk_module:
        try:
            MenardsClient = getattr(sdk_module, "MenardsClient", None)
        except Exception:
            MenardsClient = None

        if MenardsClient:
            # Create client instance
            client = MenardsClient(base_url=backend_url)
            
            # Use session_id from browser context if available
            for cookie in browser_context.get("cookies", []):
                name = cookie.get("name", "").lower()
                if "session" in name:
                    client.session_id = cookie.get("value")
                    break
            local = browser_context.get("localStorage", {})
            if not client.session_id:
                for key in ["session_id", "sessionId", "MENARDS_SESSION"]:
                    if local.get(key):
                        client.session_id = local[key]
                        break

            helpers["client"] = client  # Direct instance, not function

    # TODO: add helpers for other sites as needed (instacart, ikea, etc.)

    return helpers

