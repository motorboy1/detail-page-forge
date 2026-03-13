"""Tests for DB models and session management."""


import pytest

from detail_forge.db.models import Generation, Template, User
from detail_forge.db.session import DatabaseManager


@pytest.fixture
def db_manager():
    """In-memory SQLite DatabaseManager for tests."""
    manager = DatabaseManager(db_url="sqlite:///:memory:")
    manager.create_tables()
    yield manager
    manager.drop_tables()


@pytest.fixture
def session(db_manager):
    """Provide a DB session and roll back after each test."""
    s = db_manager.get_session()
    yield s
    s.close()


# --- DatabaseManager ---


class TestDatabaseManager:
    def test_create_tables(self, db_manager):
        """create_tables should succeed without error."""
        # Tables already created in fixture; calling again is idempotent
        db_manager.create_tables()

    def test_get_session_returns_session(self, db_manager):
        """get_session should return a usable SQLAlchemy Session."""
        s = db_manager.get_session()
        assert s is not None
        s.close()

    def test_drop_tables(self):
        """drop_tables should remove all tables."""
        manager = DatabaseManager(db_url="sqlite:///:memory:")
        manager.create_tables()
        manager.drop_tables()
        # After drop, metadata has no tables reflected in engine
        from sqlalchemy import inspect
        insp = inspect(manager.engine)
        assert insp.get_table_names() == []


# --- Template model ---


class TestTemplateModel:
    def test_create_template(self, session):
        """Should persist a Template and retrieve it by primary key."""
        tmpl = Template(
            id="tmpl-001",
            section_type="hero",
            category="fashion",
            d1000_principles=["principle_a"],
            html_path="/templates/tmpl-001.html",
            thumbnail_path="/thumbnails/tmpl-001.png",
        )
        session.add(tmpl)
        session.commit()

        retrieved = session.get(Template, "tmpl-001")
        assert retrieved is not None
        assert retrieved.id == "tmpl-001"
        assert retrieved.section_type == "hero"
        assert retrieved.category == "fashion"
        assert retrieved.d1000_principles == ["principle_a"]

    def test_template_defaults(self, session):
        """Template should apply sensible defaults for optional fields."""
        tmpl = Template(id="tmpl-defaults")
        session.add(tmpl)
        session.commit()

        retrieved = session.get(Template, "tmpl-defaults")
        assert retrieved.section_type == "hero"
        assert retrieved.category == ""
        assert retrieved.d1000_principles == []
        assert retrieved.html_path == ""
        assert retrieved.thumbnail_path == ""
        assert retrieved.created_at is not None

    def test_template_repr(self):
        """Template repr should include id and section_type."""
        tmpl = Template(id="x", section_type="features")
        assert "x" in repr(tmpl)
        assert "features" in repr(tmpl)

    def test_delete_template(self, session):
        """Should be able to delete a Template."""
        tmpl = Template(id="tmpl-delete")
        session.add(tmpl)
        session.commit()

        session.delete(tmpl)
        session.commit()

        assert session.get(Template, "tmpl-delete") is None

    def test_multiple_templates(self, session):
        """Should store multiple Template records."""
        for i in range(3):
            session.add(Template(id=f"tmpl-multi-{i}", section_type="hero"))
        session.commit()

        count = session.query(Template).count()
        assert count == 3


# --- Generation model ---


class TestGenerationModel:
    def test_create_generation(self, session):
        """Should persist a Generation and retrieve it."""
        gen = Generation(
            product_name="Running Shoes X200",
            template_ids=["tmpl-001", "tmpl-002"],
            theme_name="classic_trust",
            quality_score=0.87,
            generation_time_ms=1250,
            output_path="/output/gen-001.html",
        )
        session.add(gen)
        session.commit()

        retrieved = session.get(Generation, gen.id)
        assert retrieved is not None
        assert retrieved.product_name == "Running Shoes X200"
        assert retrieved.quality_score == pytest.approx(0.87)
        assert retrieved.generation_time_ms == 1250
        assert retrieved.template_ids == ["tmpl-001", "tmpl-002"]

    def test_generation_defaults(self, session):
        """Generation should apply default values."""
        gen = Generation(product_name="Test Product")
        session.add(gen)
        session.commit()

        retrieved = session.get(Generation, gen.id)
        assert retrieved.theme_name == "classic_trust"
        assert retrieved.quality_score == pytest.approx(0.0)
        assert retrieved.generation_time_ms == 0
        assert retrieved.output_path == ""
        assert retrieved.template_ids == []
        assert retrieved.created_at is not None

    def test_generation_autoincrement(self, session):
        """Generation IDs should autoincrement."""
        g1 = Generation(product_name="Product A")
        g2 = Generation(product_name="Product B")
        session.add_all([g1, g2])
        session.commit()

        assert g2.id == g1.id + 1

    def test_generation_repr(self):
        """Generation repr should include product_name."""
        gen = Generation(product_name="Shoe")
        assert "Shoe" in repr(gen)

    def test_delete_generation(self, session):
        """Should be able to delete a Generation."""
        gen = Generation(product_name="Delete Me")
        session.add(gen)
        session.commit()
        gen_id = gen.id

        session.delete(gen)
        session.commit()

        assert session.get(Generation, gen_id) is None


# --- User model ---


class TestUserModel:
    def test_create_user(self, session):
        """Should persist a User and retrieve it."""
        user = User(email="alice@example.com", name="Alice")
        session.add(user)
        session.commit()

        retrieved = session.get(User, user.id)
        assert retrieved is not None
        assert retrieved.email == "alice@example.com"
        assert retrieved.name == "Alice"
        assert retrieved.created_at is not None

    def test_user_defaults(self, session):
        """User name should default to empty string."""
        user = User(email="bob@example.com")
        session.add(user)
        session.commit()

        retrieved = session.get(User, user.id)
        assert retrieved.name == ""

    def test_user_email_unique(self, session):
        """Duplicate email should raise an IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        session.add(User(email="dup@example.com"))
        session.commit()

        session.add(User(email="dup@example.com"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_user_repr(self):
        """User repr should include email."""
        user = User(email="test@test.com")
        assert "test@test.com" in repr(user)

    def test_delete_user(self, session):
        """Should be able to delete a User."""
        user = User(email="todelete@example.com")
        session.add(user)
        session.commit()
        user_id = user.id

        session.delete(user)
        session.commit()

        assert session.get(User, user_id) is None

    def test_multiple_users(self, session):
        """Should store multiple User records with unique emails."""
        for i in range(5):
            session.add(User(email=f"user{i}@example.com", name=f"User {i}"))
        session.commit()

        count = session.query(User).count()
        assert count == 5
