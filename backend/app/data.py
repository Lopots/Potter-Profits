from .schemas import DashboardResponse, MarketSnapshot, ModelLayer, PortfolioSummary, PotterState, RiskGuardrail


def build_model_layers() -> list[ModelLayer]:
    return [
        ModelLayer(
            name="Deterministic Pricing Engine",
            role="Primary decision layer",
            weight="Highest weight",
            purpose="Convert odds to probability, compare markets, filter weak edges, and establish the base trade thesis.",
            examples=[
                "Implied probability conversion",
                "Cross-venue mispricing checks",
                "Liquidity and spread filters",
            ],
        ),
        ModelLayer(
            name="ML Confidence Layer",
            role="Secondary validation layer",
            weight="Medium weight",
            purpose="Score whether a detected edge historically behaves like signal or noise before execution.",
            examples=[
                "Logistic regression confidence lift",
                "Trend and volume regime checks",
                "Historical edge quality scoring",
            ],
        ),
        ModelLayer(
            name="Potter AI Analysis Layer",
            role="Supporting context layer",
            weight="Lowest weight",
            purpose="Turn news, sentiment, and event text into structured adjustments without making the primary prediction.",
            examples=[
                "Headline batching",
                "Sentiment extraction",
                "Catalyst and injury detection",
            ],
        ),
    ]


def build_empty_dashboard() -> DashboardResponse:
    return DashboardResponse(
        snapshot=MarketSnapshot(
            total_markets=0,
            buy_signals=0,
            sell_signals=0,
            average_edge=0.0,
            strongest_edge=0.0,
        ),
        model_layers=build_model_layers(),
        markets=[],
        potter=PotterState(
            mode="paper",
            autonomy_level="paper-auto",
            mission="Monitor active markets, build true probabilities, and wait for live data before recommending trades.",
            reasoning_summary="No live market rows are currently available, so Potter is intentionally blank instead of showing sample data.",
            next_action="Restore live ingestion or rerun the market pipeline so Potter has real markets to score.",
            guardrails=[
                RiskGuardrail(
                    name="No Mock Data",
                    status="active",
                    detail="Potter will show real live rows or an empty state only.",
                )
            ],
            thoughts=[],
        ),
        trades=[],
        portfolio=PortfolioSummary(
            starting_bankroll=10000.0,
            bank_balance=10000.0,
            active_capital=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            total_equity=10000.0,
            completed_trades=0,
            open_positions=0,
            performance_points=[],
        ),
    )


def load_dashboard() -> DashboardResponse:
    return build_empty_dashboard()


def build_seed_news_items() -> list[dict[str, str | float]]:
    return [
        {
            "external_id": "news-btc-001",
            "source": "newsapi",
            "title": "Bitcoin demand rises as ETF flows strengthen into quarter end",
            "summary": "Institutional demand remains firm and supports higher implied crypto probabilities.",
            "url": "https://example.com/news/btc-demand",
            "market_external_id": "btc-80k-june",
            "relevance_score": 0.88,
        },
        {
            "external_id": "news-fed-001",
            "source": "newsapi",
            "title": "Fed speakers signal patience as inflation remains sticky",
            "summary": "Rate-cut expectations cool slightly after a more cautious policy tone.",
            "url": "https://example.com/news/fed-patience",
            "market_external_id": "fed-cut-september",
            "relevance_score": 0.82,
        },
        {
            "external_id": "news-eth-001",
            "source": "newsapi",
            "title": "Ethereum ETF flows show steady accumulation trend",
            "summary": "ETF-related headlines remain constructive and support the bullish demand narrative.",
            "url": "https://example.com/news/eth-etf",
            "market_external_id": "eth-etf-q3",
            "relevance_score": 0.84,
        },
        {
            "external_id": "news-knicks-001",
            "source": "newsapi",
            "title": "Injury concerns weigh on Knicks playoff outlook",
            "summary": "Recent injury and matchup news modestly worsen the team outlook.",
            "url": "https://example.com/news/knicks-injury",
            "market_external_id": "knicks-east-finals",
            "relevance_score": 0.79,
        },
    ]
