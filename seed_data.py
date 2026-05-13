"""Seed script — populates SQLite DB with demo data + builds FAISS vector store."""
from __future__ import annotations
from datetime import datetime, timedelta
from nexus.tools.database import init_db, Base, engine, Customer, Order, get_session
from nexus.tools.vector_store import vector_store
from rich.console import Console
from rich.panel import Panel

console = Console()


def seed_customers(session):
    customers = [
        Customer(customer_id="CUST-DEMO-001", name="Alex Johnson", email="alex@example.com", tier="premium"),
        Customer(customer_id="CUST-DEMO-002", name="Priya Sharma",  email="priya@example.com", tier="standard"),
        Customer(customer_id="CUST-DEMO-003", name="Marcus Lee",    email="marcus@example.com", tier="standard"),
        Customer(customer_id="CUST-DEMO-004", name="Sarah Chen",    email="sarah@example.com", tier="premium"),
        Customer(customer_id="CUST-DEMO-005", name="James Wilson",  email="james@example.com", tier="standard"),
    ]
    for c in customers:
        if not session.get(Customer, c.customer_id):
            session.add(c)
    session.commit()
    console.print(f"  ✓ Seeded {len(customers)} customers", style="green")


def seed_orders(session):
    now = datetime.utcnow()
    orders = [
        Order(
            order_id="ORD-001", customer_id="CUST-DEMO-001",
            status="shipped", item_name="Sony WH-1000XM5 Headphones",
            item_category="electronics", amount=349.99,
            tracking_number="794644792798", carrier="fedex",
            placed_at=now - timedelta(days=3),
            shipped_at=now - timedelta(days=2),
            estimated_delivery=now + timedelta(days=1),
        ),
        Order(
            order_id="ORD-002", customer_id="CUST-DEMO-001",
            status="delivered", item_name="Nike Air Max 270",
            item_category="clothing", amount=89.99,
            tracking_number="1Z999AA10123456784", carrier="ups",
            placed_at=now - timedelta(days=12),
            shipped_at=now - timedelta(days=10),
            estimated_delivery=now - timedelta(days=7),
        ),
        Order(
            order_id="ORD-003", customer_id="CUST-DEMO-002",
            status="processing", item_name="MacBook Air M3",
            item_category="electronics", amount=1299.00,
            placed_at=now - timedelta(days=1),
        ),
        Order(
            order_id="ORD-004", customer_id="CUST-DEMO-003",
            status="out_for_delivery", item_name="Instant Pot Duo 7-in-1",
            item_category="kitchen", amount=79.95,
            tracking_number="9400111899223397487318", carrier="usps",
            placed_at=now - timedelta(days=5),
            shipped_at=now - timedelta(days=4),
            estimated_delivery=now,
        ),
        Order(
            order_id="ORD-005", customer_id="CUST-DEMO-004",
            status="delivered", item_name="Adobe Creative Cloud (1 year)",
            item_category="digital_downloads", amount=599.88,
            placed_at=now - timedelta(days=45),
        ),
        Order(
            order_id="ORD-006", customer_id="CUST-DEMO-005",
            status="cancelled", item_name="Samsung 65-inch QLED TV",
            item_category="electronics", amount=999.99,
            placed_at=now - timedelta(days=2),
        ),
        Order(
            order_id="ORD-007", customer_id="CUST-DEMO-002",
            status="shipped", item_name="Levi's 501 Original Jeans",
            item_category="clothing", amount=59.50,
            tracking_number="420101019361289878750119136342", carrier="usps",
            placed_at=now - timedelta(days=4),
            shipped_at=now - timedelta(days=3),
            estimated_delivery=now + timedelta(days=2),
        ),
        Order(
            order_id="ORD-008", customer_id="CUST-DEMO-003",
            status="delivered", item_name="Python Crash Course (Book)",
            item_category="books", amount=35.99,
            placed_at=now - timedelta(days=20),
            shipped_at=now - timedelta(days=19),
            estimated_delivery=now - timedelta(days=16),
        ),
    ]
    for o in orders:
        if not session.get(Order, o.order_id):
            session.add(o)
    session.commit()
    console.print(f"  ✓ Seeded {len(orders)} orders (all statuses covered)", style="green")


def main():
    console.print(Panel.fit(
        "[bold cyan]NEXUS Seed Script[/bold cyan]\nInitializing database and vector store...",
        border_style="cyan",
    ))

    # ── Database ───────────────────────────────────────────────────────────────
    console.print("\n[bold]1. Database[/bold]")
    init_db()
    console.print("  ✓ Tables created", style="green")

    with get_session() as session:
        seed_customers(session)
        seed_orders(session)

    # ── Vector store ───────────────────────────────────────────────────────────
    console.print("\n[bold]2. Vector Store (FAISS)[/bold]")
    console.print("  Building embeddings from 15 FAQ policy documents...")
    vector_store.build()
    console.print("  ✓ FAISS index built and saved to disk", style="green")

    # ── Done ───────────────────────────────────────────────────────────────────
    console.print(Panel.fit(
        "[bold green]✅ Setup complete![/bold green]\n\n"
        "Start the backend:   [cyan]uvicorn nexus.api.main:app --reload --port 8000[/cyan]\n"
        "Start the frontend:  [cyan]streamlit run app.py[/cyan]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
