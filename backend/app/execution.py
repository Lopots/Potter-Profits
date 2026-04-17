from app.core.config import settings


def get_execution_status() -> dict[str, object]:
    return {
        "paper_trading_enabled": settings.kalshi_paper_trading,
        "live_trading_enabled": settings.live_trading_enabled,
        "execution_venue": "kalshi",
        "max_paper_trade_size": settings.max_paper_trade_size,
        "max_live_trade_size": settings.max_live_trade_size,
        "daily_loss_limit": settings.daily_loss_limit,
        "live_trading_lock_reason": (
            None
            if settings.live_trading_enabled
            else "Live trading is locked. Enable it only after paper results, audit logs, and venue execution checks are verified."
        ),
    }
