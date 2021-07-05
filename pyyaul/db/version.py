"""
Database Versioning Class
"""

try:
	from pyyaul.base.version import Version as _VersionBase
except ImportError
	print('Error importing PyYAUL.Base...please make sure it is installed and in `sys.path`.')
	raise
try:
	from sqlalchemy import Column, Integer, String
	from sqlalchemy.schema import MetaData, Table
except:
	print('Failed to find SQLAlchemy installed.  Some features of `pyyaul.db.version` will be unavailable.')
	sqlalchemy = None




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

				clsPrev = None
				#Set `clsPrev` to the `pyyaul.base.version.Version` CLASS
				#matching the previous schema version for your database.

				def _initMetaData(self, metadata):
					Table(
						'user',
						metadata,
						Column('id', Integer, primary_key=True),
						Column('email', String(100), unique=True),
						Column('password', String(100)),
						Column('name', String(1000)),
						schema='accounts',
					)
		@endcode

		You can then pass a SQLAlchemy `Engine` object to the other methods to:

			- Check the DB version.
			- Update the DB to a newer version.
			- Initialize the DB from scratch to match this version.
		"""

		metadata = None  #`sqlalchemy.schema.metadata` object storing the schema definition.

		def __init__(self):
			self.metadata = MetaData()
			self._initMetaData(self.metadata)

		def _initMetaData(self, metadata):
			"""
			Populates `metadata` with the schema for this database version.
			"""
			raise NotImplementedError()

		def matches(self, engine):
			"""
			Tests the database behind `engine` and returns `True` if it matches this
			version.
			"""
			engineMetadata = MetaData()
			for schemaTable in self._tables:
				engineTable = Table(
					schemaTable.name,
					engineMetadata,
					autoload_with=engine,
					schema=schemaTable.schema,
				)
				if not self.compareTables(engineTable, schemaTable):
					return False
			return True

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
			if not(lhs.primary_key) and lhs.server_default != rhs.server_default:
				print(f'Columns have different `server_default` values: {lhs.server_default=}; {rhs.server_default=}')
				return False
			if lhs.server_onupdate != rhs.server_onupdate:
				print(f'Columns have different `server_onupdate` values: {lhs.server_onupdate=}; {rhs.server_onupdate=}')
				return False
			if type(lhs.type.as_generic()) != type(rhs.type.as_generic()):
				print(f'Columns have different types: {type(lhs.type.as_generic())=}; {type(rhs.type.as_generic())=}')
				return False
			if isinstance(lhs.type.as_generic(), String):
				if lhs.type.length != rhs.type.length:
					print(f'Columns have different lengths: {lhs.type.length=}; {rhs.type.length=}')
					return False
			elif isinstance(lhs.type.as_generic(), Integer):
				pass
			else:
				print(f'Columns have unexpected type: {lhs.type.as_generic()=}')
				return False
			return True
