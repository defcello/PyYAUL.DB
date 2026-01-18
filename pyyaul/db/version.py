"""
Database Versioning Class
"""

try:
    from pyyaul.base.version import Version as _VersionBase
except ImportError:
    print('Error importing PyYAUL.Base...please make sure it is installed and in `sys.path`.')
    raise
try:
    import sqlalchemy
    from sqlalchemy import Boolean, Column, Integer, String, text
    from sqlalchemy.engine import Connection
    from sqlalchemy.engine.base import Engine
    from sqlalchemy.schema import MetaData, Table
except ImportError:
    print('Failed to find SQLAlchemy installed.  Some features of `pyyaul.db.version` will be unavailable.')
    sqlalchemy = None
from textwrap import dedent as d




if sqlalchemy is not None:

    class Version(_VersionBase):

        """
        Database Versioning Class for SQLAlchemy.

        Subclass this and overload `_initMetaData` with code that populated the
        given `metadata` parameter with the database schema.

        @code
            from pyyaul.db.version import Version
            from sqlalchemy import Column, Integer, String
            from sqlalchemy.schema import Table

            class SchemaV0(Version):

                def _initMetaData(self, metadata):
                    Table(
                        'user',
                        metadata,
                        Column('id', Integer, primary_key=True),
                        Column('email', String(100), unique=True),
                        Column('password', String(100)),
                        Column('username', String(1000)),
                        schema='accounts',
                    )

            class SchemaV1(Version):

                clsPrev = SchemaV0

                def _initMetaData(self, metadata):
                    Table(
                        'user',
                        metadata,
                        Column('id', Integer, primary_key=True),
                        Column('email', String(100), unique=True),
                        Column('password', String(100)),
                        Column('username', String(1000)),
                        Column('displayname', String(1000)),
                        schema='accounts',
                    )

                def _update(self, engine):
                    self._updateAddColumn(
                        engine,
                        self.metadata.tables['user'],
                        self.metadata.tables['user'].columns['displayname'],
                    );
                    Table(
                        'user',
                        metadata,
                        Column('id', Integer, primary_key=True),
                        Column('email', String(100), unique=True),
                        Column('password', String(100)),
                        Column('username', String(1000)),
                        Column('displayname', String(1000)),
                        schema='accounts',
                    )
        @endcode

        You can then pass a SQLAlchemy `Engine` object to the other methods to:

            - Check the DB version.
            - Update the DB to a newer version.
            - Initialize the DB from scratch to match this version.
        """

        clsPrev = None
        #Set `clsPrev` to the `pyyaul.base.version.Version` CLASS
        #matching the previous schema version for your database.

        metadata = None  #`sqlalchemy.schema.metadata` object storing the schema definition.

        def __init__(self):
            super().__init__()
            self.metadata = MetaData()
            self._initMetaData(self.metadata)

        def compareTables(self, lhs, rhs):
            if lhs.name != rhs.name:
                print(f'Tables do not match: {lhs.name=}; {rhs.name=}')
                return False
            for (lhsColumn, rhsColumn) in zip(lhs.columns.values(), rhs.columns.values()):
                if not self.compareColumns(lhsColumn, rhsColumn):
                    return False
            return True

        def compareColumns(self, lhs, rhs):
            if lhs.name != rhs.name:
                print(f'Columns do not match: {lhs.name=}; {rhs.name=}')
                return False
            if lhs.primary_key != rhs.primary_key:
                print(f'Columns have different `primary_key` states: {lhs.primary_key=}; {rhs.primary_key=}')
                return False
            #`reflect` does not capture this.  Will have to use `Inspector`: https://stackoverflow.com/a/33898867/2201287
            # if lhs.unique != rhs.unique:
                # print(f'Columns have different `unique` states: {lhs.unique=}; {rhs.unique=}')
                # return False
            if not(lhs.primary_key) and lhs.server_default != rhs.server_default:
                if lhs.server_default is not None and rhs.server_default is not None and lhs.server_default.has_argument and rhs.server_default.has_argument:
                    try:
                        if str(lhs.server_default.arg) != str(rhs.server_default.arg):
                            print(
                                f'Columns have different `server_default.arg` values: lhs.server_default.arg = {str(lhs.server_default.arg)}; rhs.server_default.arg = {str(rhs.server_default.arg)}'
                            )
                            return False
                    except:
                        print(f'Columns have different `server_default` values: {lhs.server_default=}; {rhs.server_default=}')
                        return False
                else:
                    print(f'Columns have different `server_default` values: {lhs.server_default=}; {rhs.server_default=}')
                    return False
            if lhs.server_onupdate != rhs.server_onupdate:
                print(f'Columns have different `server_onupdate` values: {lhs.server_onupdate=}; {rhs.server_onupdate=}')
                return False
            if type(lhs.type.as_generic()) != type(rhs.type.as_generic()):
                print(f'Columns have different types: {type(lhs.type.as_generic())=}; {type(rhs.type.as_generic())=}')
                return False
            if isinstance(lhs.type.as_generic(), (Boolean, Integer)):
                pass  #No additional processing required.
            elif isinstance(lhs.type.as_generic(), sqlalchemy.types.DateTime):
                if lhs.type.timezone != rhs.type.timezone:
                    print(f'Columns have different timezone settings: {lhs.type.timezone=}; {rhs.type.timezone=}')
                    return False
            elif isinstance(lhs.type.as_generic(), String):
                if lhs.type.length != rhs.type.length:
                    print(f'Columns have different lengths: {lhs.type.length=}; {rhs.type.length=}')
                    return False
            else:
                print(f'Columns have unexpected type: {lhs.type.as_generic()=}')
                return False
            return True

        def _initMetaData(self, metadata):
            """
            Populates `metadata` with the schema for this database version.

            Subclasses should override this method.
            """
            raise NotImplementedError()

        def _initialize(self, engine :Engine) ->Engine:
            """
            Initializes the database in engine to have the entities described in
            `self.metadata`.
            """
            self.metadata.create_all(engine)
            return engine

        def matches(self, engine :Engine) ->bool:
            """
            Tests the database behind `engine` and returns `True` if it matches this
            version.
            """
            ret = True
            engineMetadata = MetaData()
            schemas = {schemaTable.schema for schemaTable in self.metadata.tables.values()}
            for schema in schemas:
                engineMetadata.reflect(engine, schema=schema)
            for (schemaTableName, schemaTable) in self.metadata.tables.items():
                if schemaTableName in engineMetadata.tables:
                    engineTable = Table(
                        schemaTable.name,
                        engineMetadata,
                        autoload_with=engine,
                        schema=schemaTable.schema,
                    )
                    if not self.compareTables(engineTable, schemaTable):
                        print(f'DB table {schemaTableName!r} is different from schema.')
                        ret = False
                else:
                    print(f'DB does not have table {schemaTableName!r}.')
                    ret = False
            return ret

        def schema_create(
                self,
                connection :Connection,
                schema :str,
                replaceExisting :bool =False,
        ):
            """
            Creates the given `schema` in the database behind `connection`.

            If `replaceExisting` is `True`, any existing schema with the same
            name will be dropped and recreated.
            """
            if replaceExisting:
                try:
                    drop_schema_sql = sqlalchemy.text(d(f"""
                        DROP SCHEMA IF EXISTS {schema} CASCADE
                        ;
                    """))
                    connection.execute(drop_schema_sql)
                    print(f'Schema "{schema}": Dropped existing schema.')
                except SQLAlchemyError as e:
                    print(f'ERROR dropping existing schema "{schema}": {e}')
                    raise
            try:
                create_schema_sql = sqlalchemy.text(f'CREATE SCHEMA {schema};')
                connection.execute(create_schema_sql)
                print(f'Schema "{schema}": Created successfully.')
            except SQLAlchemyError as e:
                print(f'ERROR creating schema "{schema}": {e}')
                raise

        def schema_exists(self, connection :Connection, schema :str) ->bool:
            query = sqlalchemy.text(d(f"""
                SELECT
                    1
                    FROM information_schema.schemata
                    WHERE schema_name = :schema
                ;
            """))
            result = connection.execute(query, {'schema': schema}).fetchone()
            return result is not None

        def table_exists(self, connection :Connection, schema, table):
            query = sqlalchemy.text(d(f"""
                SELECT
                    1
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                        AND table_name = :table
                ;
            """))
            result = connection.execute(query, {'schema': schema, 'table': table}).fetchone()
            return result is not None

        def _update(self, engine :Engine) ->Engine:
            """
            Internal logic for updating `engine` to the this version.  Should
            always return the updated version of `engine`, even if `engine` is
            modified in place.

            Subclasses should override this method.
            """
            raise NotImplementedError()

        def _updateAddColumn(self, engine :Engine, table, column):
            """
            Utility method for adding a column to a table.
            """
            #Source: https://stackoverflow.com/a/17243132/2201287
            columnName = column.compile(dialect=engine.dialect)
            columnType = column.type.compile(dialect=engine.dialect)
            with engine.begin() as cursor:
                cursor.execute(text(d(f"""
                    ALTER TABLE {table.schema}.{table.name}
                        ADD COLUMN {columnName} {columnType}
                    ;
                """)))
