"""Category service."""
from dataclasses import fields
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.graphql.types.inputs import CreateCategoryInput, UpdateCategoryInput
from app.graphql.types.category import Category as GQLCategory, CategoryTree
from app.graphql.serializers import category_to_gql


class CategoryService:
    """Category service for managing event categories."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_category_tree(self, user_id: uuid.UUID) -> CategoryTree:
        """Get full category tree for user."""
        # Get all categories for user
        result = await self.db.execute(
            select(Category)
            .where(Category.user_id == user_id, Category.deleted_at.is_(None))
            .order_by(Category.sort_order, Category.name)
            .options(selectinload(Category.children))
        )
        categories = result.scalars().all()

        # Build tree
        category_map = {cat.id: cat for cat in categories}
        roots = []

        for cat in categories:
            if cat.parent_id is None:
                roots.append(cat)
            elif cat.parent_id in category_map:
                parent = category_map[cat.parent_id]
                # Children are already loaded via selectinload

        # Convert to GraphQL types
        gql_categories = [category_to_gql(cat) for cat in categories]
        gql_roots = [category_to_gql(cat) for cat in roots]

        return CategoryTree(
            categories=gql_roots,
            flat_list=gql_categories,
        )

    async def get_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> Optional[GQLCategory]:
        """Get category by ID."""
        result = await self.db.execute(
            select(Category)
            .where(
                Category.id == category_id,
                Category.user_id == user_id,
                Category.deleted_at.is_(None),
            )
            .options(selectinload(Category.children))
        )
        category = result.scalar_one_or_none()

        if not category:
            return None

        return category_to_gql(category)

    async def create_category(self, user_id: uuid.UUID, input: CreateCategoryInput) -> GQLCategory:
        """Create a new category."""
        # Verify parent exists and belongs to user
        if input.parent_id:
            result = await self.db.execute(
                select(Category).where(
                    Category.id == input.parent_id,
                    Category.user_id == user_id,
                    Category.deleted_at.is_(None),
                )
            )
            parent = result.scalar_one_or_none()
            if not parent:
                raise ValueError("Parent category not found")

        # Get max sort_order for this level
        if input.parent_id:
            result = await self.db.execute(
                select(func.max(Category.sort_order))
                .where(Category.parent_id == input.parent_id, Category.deleted_at.is_(None))
            )
        else:
            result = await self.db.execute(
                select(func.max(Category.sort_order))
                .where(Category.parent_id.is_(None), Category.user_id == user_id, Category.deleted_at.is_(None))
            )
        max_sort = result.scalar() or -1

        category = Category(
            user_id=user_id,
            parent_id=input.parent_id,
            name=input.name,
            description=input.description,
            color=input.color,
            icon=input.icon,
            default_reminder_minutes=input.default_reminder_minutes or [1440, 60, 15],
            sort_order=max_sort + 1,
        )

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)

        return category_to_gql(category)

    async def update_category(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        input: UpdateCategoryInput,
    ) -> GQLCategory:
        """Update a category."""
        result = await self.db.execute(
            select(Category)
            .where(
                Category.id == category_id,
                Category.user_id == user_id,
                Category.deleted_at.is_(None),
            )
            .options(selectinload(Category.children))
        )
        category = result.scalar_one_or_none()

        if not category:
            raise ValueError("Category not found")

        if category.is_system:
            raise ValueError("Cannot modify system categories")

        # Update fields
        update_data = {
            field.name: getattr(input, field.name)
            for field in fields(input)
            if getattr(input, field.name) is not None
        }
        for field, value in update_data.items():
            setattr(category, field, value)

        await self.db.commit()
        await self.db.refresh(category)

        return category_to_gql(category)

    async def delete_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        """Delete a category (soft delete)."""
        result = await self.db.execute(
            select(Category)
            .where(
                Category.id == category_id,
                Category.user_id == user_id,
                Category.deleted_at.is_(None),
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            raise ValueError("Category not found")

        if category.is_system:
            raise ValueError("Cannot delete system categories")

        # Soft delete
        category.deleted_at = datetime.now(timezone.utc)

        # Also soft delete children
        await self._soft_delete_children(category_id)

        await self.db.commit()
        return True

    async def _soft_delete_children(self, parent_id: uuid.UUID) -> None:
        """Recursively soft delete child categories."""
        result = await self.db.execute(
            select(Category).where(Category.parent_id == parent_id, Category.deleted_at.is_(None))
        )
        children = result.scalars().all()

        for child in children:
            child.deleted_at = datetime.now(timezone.utc)
            await self._soft_delete_children(child.id)

    async def reorder_categories(self, user_id: uuid.UUID, category_ids: List[uuid.UUID]) -> List[GQLCategory]:
        """Reorder categories."""
        # Verify all categories belong to user
        result = await self.db.execute(
            select(Category).where(
                Category.id.in_(category_ids),
                Category.user_id == user_id,
                Category.deleted_at.is_(None),
            )
        )
        categories = {cat.id: cat for cat in result.scalars().all()}

        if len(categories) != len(category_ids):
            raise ValueError("One or more categories not found")

        # Update sort_order
        for index, cat_id in enumerate(category_ids):
            categories[cat_id].sort_order = index

        await self.db.commit()

        # Return updated categories
        gql_categories = []
        for cat_id in category_ids:
            await self.db.refresh(categories[cat_id])
            gql_categories.append(category_to_gql(categories[cat_id]))

        return gql_categories
