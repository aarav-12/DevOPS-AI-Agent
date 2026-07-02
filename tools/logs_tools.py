def search_logs_impl(query: str, service: str = "", since_minutes: int = 60) -> str:
    svc_tag = f"[{service}] " if service else ""
    return (
        f"Log search: '{query}' {svc_tag}(last {since_minutes}m)\n"
        "2026-07-02T14:01:12Z ERROR connection refused: postgres://payments-db:5432\n"
        "2026-07-02T14:01:09Z ERROR connection refused: postgres://payments-db:5432\n"
        "2026-07-02T14:01:06Z ERROR connection refused: postgres://payments-db:5432\n"
        "3 matches found."
    )


def get_error_rate_impl(service: str, window_minutes: int = 5) -> str:
    rates = {
        "payments-service": "18.3%",
        "orders-service":   "0.02%",
        "auth-service":     "0.01%",
    }
    rate = rates.get(service, "unknown service — check service name")
    return f"{service} error rate (last {window_minutes}m): {rate}"
