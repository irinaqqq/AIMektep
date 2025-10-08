from pydantic import BaseModel
from fastapi import HTTPException
from typing import Any, Generic, Optional, Type, TypeVar, Union

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Base
from core.logger import logger

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic CRUD base class for SQLAlchemy models.
    Provides create, read, update, delete operations with helpful error messages.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize with a SQLAlchemy model class.
        """
        self.model = model

    def _raise_not_found_if_empty(self, obj, detail=None, **kwargs):
        """
        Raises HTTPException 404 if the object or list is empty/None.
        The detail message is formed as '<ModelName> with field1=val1, field2=val2 not found'.
        """
        if obj is None or (isinstance(obj, list) and not obj):
            if detail is None:
                model_name = self.model.__name__
                if kwargs:
                    conditions = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
                    detail = f"{model_name} with {conditions} not found"
                else:
                    detail = f"{model_name} not found"
            raise HTTPException(status_code=404, detail=detail)
        return obj


    async def create(self, db: AsyncSession, obj_in: Union[CreateSchemaType, dict[str, Any]]) -> ModelType:
        """
        Create a new object from input schema or dict.
        """
        logger.debug(f"Creating {self.model.__name__} with data: {obj_in}")
        obj_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.flush()
        return db_obj


    async def get(
        self, 
        db: AsyncSession, 
        id: Any, 
        options: Optional[list[Any]] = None
    ) -> ModelType:
        """
        Get object by primary key (id).
        If options are provided, loads related objects (e.g. selectinload()).
        Raises 404 if not found.
        """
        logger.debug(f"Fetching {self.model.__name__} by primary key id={id} with options={options}")

        if options:
            stmt = select(self.model).options(*options).filter_by(id=id)
            result = await db.execute(stmt)
            obj = result.scalars().first()
        else:
            obj = await db.get(self.model, id)

        return self._raise_not_found_if_empty(obj, id=id)


    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100, options: Optional[list[Any]] = None) -> list[ModelType]:
        """
        Retrieve multiple objects (paginated).
        Returns an empty list if none found.
        """
        logger.debug(f"Fetching multiple {self.model.__name__} entries: skip={skip}, limit={limit}")
        stmt = select(self.model).offset(skip).limit(limit)
        if options:
            stmt = stmt.options(*options)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_objects(self, db: AsyncSession, return_many: bool = False, options: Optional[list[Any]] = None, **kwargs) -> Union[ModelType, list[ModelType]]:
        """
        Universal search for objects by one or more fields.
        If return_many=False (default), returns the first found object (or raises 404 if not found).
        If return_many=True, returns a list of all found objects (or raises 404 if none found).
        Raises 400 if any field is invalid.
        Also can get objects with options.
        """
        invalid_fields = [k for k in kwargs if k not in self.model.__table__.columns]
        if invalid_fields:
            raise HTTPException(status_code=400, detail=f"Invalid field(s): {', '.join(invalid_fields)}")
        logger.debug(f"Fetching {'all' if return_many else 'one'} {self.model.__name__} by fields: {kwargs}")

        stmt = select(self.model).filter_by(**kwargs)
        if options:
            stmt = stmt.options(*options)

        result = await db.execute(stmt)
        if return_many:
            objects = result.scalars().all()
            return self._raise_not_found_if_empty(objects, **kwargs)
        else:
            obj = result.scalars().first()
            return self._raise_not_found_if_empty(obj, **kwargs)


    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, dict[str, Any]]) -> ModelType:
        """
        Update an existing object with input schema or dict.
        Only fields present in input will be updated.
        """
        logger.debug(f"Updating {self.model.__name__} with data: {obj_in}")
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.flush()
        return db_obj


    async def remove(self, db: AsyncSession, id: int) -> ModelType:
        """
        Remove an object by primary key.
        Raises 404 if not found.
        """
        logger.debug(f"Removing {self.model.__name__} with id: {id}")
        obj = await self.get(db, id)
        await db.delete(obj)
        await db.flush()
        return obj


    async def remove_by_field(self, db: AsyncSession, **kwargs) -> ModelType:
        """
        Remove a single object by field(s) and value(s).
        Raises 404 if not found or 400 if any field is invalid.
        """
        logger.debug(f"Removing {self.model.__name__} entry by fields: {kwargs}")
        obj = await self.get_objects(db, **kwargs)
        await db.delete(obj)
        await db.flush()
        return obj
    

    async def count(self, db: AsyncSession) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await db.execute(stmt)
        return result.scalar_one()