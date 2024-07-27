"""
Database Versioning Class
"""

try:
    import sqlalchemy
    from sqlalchemy import create_engine, MetaData
    from sqlalchemy.orm import sessionmaker, declarative_base
except ImportError:
    print('Failed to find SQLAlchemy installed.  Some features of `pyyaul.db.version` will be unavailable.')
    sqlalchemy = None




if sqlalchemy is not None:

    class ORM:

        """
        Automates the construction of an ORM interface to the database behind
        `engine`.
        """

        engine =None  #`engine` supplied to the constructor.
        metadata :MetaData|None =None  #Reflected `MetaData` object.
        declarative_base =None  #Base class to use for ORM classes.
        tables :dict[str: declarative_base]  #Mapping of table names to their corresponding ORM classes.

        def __init__(self, engine, schema :str|None =None):
            self.engine = engine
            import _execommon
            self.metadata = MetaData(schema=schema)
            self.metadata.reflect(bind=self.engine)
            self.declarative_base = declarative_base(metadata=self.metadata)
            self.tables = self._tables_init()

        def session(self):
            """
            Returns a `Session` object bound to `self.engine`.

            Recommend using as `with ORM.session() as dbSession:`.
            """
            return sessionmaker(bind=self.engine)()

        def _tables_init(self):
            tables = {}
            for table_name, table in self.metadata.tables.items():
                orm_class = type(f'ORM_{table_name}', (self.declarative_base,), {'__table__': table})
                tables[table_name] = orm_class
            return tables
