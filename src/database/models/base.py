import datetime
import enum

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.collections import InstrumentedList


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    def to_dict(self, include_relations: bool = False, visited=None) -> dict:
        """
        Converts model instance to dict, optionally including relationships.
        Prevents recursion using `visited` set.
        """
        if visited is None:
            visited = set()

        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, (datetime.date, datetime.datetime)):
                value = value.isoformat()
            elif isinstance(value, enum.Enum):
                value = value.value
            data[column.name] = value

        if include_relations:
            visited.add(id(self))
            for attr in self.__mapper__.relationships:
                related = getattr(self, attr.key)
                if related is None:
                    continue
                if isinstance(related, InstrumentedList):
                    data[attr.key] = [
                        obj.to_dict(include_relations=False, visited=visited)
                        for obj in related
                        if id(obj) not in visited
                    ]
                elif id(related) not in visited:
                    data[attr.key] = related.to_dict(include_relations=False, visited=visited)

        return data
