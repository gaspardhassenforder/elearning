#!/usr/bin/env python3
"""
Seed test admin and learner accounts with a test company for local development.

Creates:
- A test company (Acme Corp, slug: acme)
- Admin user (admin / changeme) if no users exist
- Learner user (learner / learner123) with company assignment
- Optional: one published notebook assigned to the company so the learner has a module

Requires .env (or SURREAL_* env vars) and SurrealDB to be reachable.
JWT_SECRET_KEY must be set for auth to work (same as API).

Usage:
  uv run python scripts/seed_test_accounts.py
  uv run python scripts/seed_test_accounts.py --no-notebook   # skip creating a sample module
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# Ensure project root is on path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# Default test credentials (override with env if needed)
DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "changeme")
DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@localhost")
DEFAULT_LEARNER_USERNAME = os.environ.get("TEST_LEARNER_USERNAME", "learner")
DEFAULT_LEARNER_PASSWORD = os.environ.get("TEST_LEARNER_PASSWORD", "learner123")
DEFAULT_LEARNER_EMAIL = os.environ.get("TEST_LEARNER_EMAIL", "learner@localhost")
TEST_COMPANY_NAME = os.environ.get("TEST_COMPANY_NAME", "Acme Corp")
TEST_COMPANY_SLUG = os.environ.get("TEST_COMPANY_SLUG", "acme")
TEST_NOTEBOOK_NAME = os.environ.get("TEST_NOTEBOOK_NAME", "Welcome Module")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed test admin and learner accounts")
    parser.add_argument(
        "--no-notebook",
        action="store_true",
        help="Do not create a sample notebook/module for the learner",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Update existing learner to have test company if they have no company",
    )
    args = parser.parse_args()

    from api.auth import hash_password, is_jwt_enabled
    from open_notebook.domain.user import User
    from open_notebook.domain.company import Company
    from open_notebook.domain.notebook import Notebook
    from open_notebook.domain.module_assignment import ModuleAssignment
    from api.assignment_service import assign_module

    if not is_jwt_enabled():
        print("JWT not enabled (JWT_SECRET_KEY not set). Set it in .env to use auth.")
        sys.exit(1)

    # 1. Ensure test company exists
    company = await Company.get_by_slug(TEST_COMPANY_SLUG)
    if not company:
        company = Company(name=TEST_COMPANY_NAME, slug=TEST_COMPANY_SLUG)
        await company.save()
        print(f"Created company: {company.name} (slug: {TEST_COMPANY_SLUG})")
    else:
        print(f"Company already exists: {company.name}")

    # 2. Ensure admin user exists (only if no users at all)
    existing_users = await User.get_all()
    if not existing_users:
        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role="admin",
        )
        await admin.save()
        print(f"Created admin user: {DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}")
    else:
        admin = await User.get_by_username(DEFAULT_ADMIN_USERNAME)
        if not admin:
            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                role="admin",
            )
            await admin.save()
            print(f"Created admin user: {DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}")
        else:
            print(f"Admin user already exists: {DEFAULT_ADMIN_USERNAME}")

    # 3. Ensure learner user exists with company_id
    learner = await User.get_by_username(DEFAULT_LEARNER_USERNAME)
    if not learner:
        learner = User(
            username=DEFAULT_LEARNER_USERNAME,
            email=DEFAULT_LEARNER_EMAIL,
            password_hash=hash_password(DEFAULT_LEARNER_PASSWORD),
            role="learner",
            company_id=company.id,
            onboarding_completed=True,
        )
        await learner.save()
        print(f"Created learner user: {DEFAULT_LEARNER_USERNAME} / {DEFAULT_LEARNER_PASSWORD} (company: {company.name})")
    elif not learner.company_id or args.force:
        learner.company_id = company.id
        learner.onboarding_completed = True
        await learner.save()
        print(f"Updated learner {DEFAULT_LEARNER_USERNAME} with company: {company.name}")
    else:
        print(f"Learner user already exists with company: {DEFAULT_LEARNER_USERNAME}")

    # 4. Optionally create one published notebook and assign to company
    if not args.no_notebook:
        # Find an existing published notebook or create one
        notebooks = await Notebook.get_all()
        sample = None
        for n in notebooks:
            if getattr(n, "published", False):
                sample = n
                break
        if not sample:
            sample = Notebook(
                name=TEST_NOTEBOOK_NAME,
                description="A sample module for testing the learning platform.",
                archived=False,
                published=True,
            )
            await sample.save()
            print(f"Created notebook: {sample.name} (published)")
        try:
            await assign_module(company.id, sample.id, assigned_by=admin.id if admin else None)
            print(f"Assigned module '{sample.name}' to company {company.name}")
        except (RuntimeError, Exception) as e:
            if "Unexpected insert" in str(e) or "already contains" in str(e):
                print(f"Module '{sample.name}' already assigned to {company.name}; skipping.")
            else:
                raise

    print("\nYou can log in with:")
    print(f"  Admin:  {DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}")
    print(f"  Learner: {DEFAULT_LEARNER_USERNAME} / {DEFAULT_LEARNER_PASSWORD}")
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
