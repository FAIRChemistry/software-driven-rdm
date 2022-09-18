from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session


def build_sql_database(*args, loc: str):
    """Builds an SQL Database from an sdRDM data model"""

    loc = f"sqlite:///{loc}"
    engine = create_engine(loc)

    if not database_exists(loc):
        create_database(loc)

    for obj in args:
        base = obj.build_orm()
        base.metadata.create_all(engine)


def add_to_database(dataset, loc: str):
    """Adds a given sdRDM dataset to an SQL Database.

    Args:
        dataset (DataModel): Dataset to add to the database
        loc (str): Location of the database
    """

    Base = automap_base(metadata=dataset.build_orm().metadata)
    Base.prepare()

    # engine, suppose it has two tables 'user' and 'address' set up
    engine = create_engine(f"sqlite:///{loc}")

    # Map dataset to ORM
    mapped = _map_to_orm(dataset, Base)

    with Session(engine) as session:
        session.add(mapped)
        session.commit()


def _map_to_orm(obj, base, tablename=None):
    """Maps values from an object to a given SQL database using an ORM"""

    if tablename is None:
        tablename = obj.__class__.__name__

    # Get the corresponding ORM class
    orm_obj = getattr(base.classes, tablename)()

    for name, value in obj:

        if isinstance(value, list):
            # Check if its an object or a simple list
            is_object = all(hasattr(sub_obj, "__fields__") for sub_obj in value)

            # Get the collection to append to
            orm_collection = getattr(orm_obj, f"{name}_collection")

            if is_object:
                for sub_obj in value:
                    orm_collection.append(_map_to_orm(sub_obj, base, tablename=name))
            else:
                for entry in value:
                    sub_orm_obj = getattr(base.classes, name)()
                    setattr(sub_orm_obj, name, entry)
                    orm_collection.append(sub_orm_obj)

        else:
            setattr(orm_obj, name, value)

    return orm_obj
