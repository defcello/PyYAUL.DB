"""
Test module for `pyyaul.db.version`.
"""

import unittest
from unittest import TestCase

import sqlalchemy
from sqlalchemy import Column, Integer, String, create_engine, inspect, select
from sqlalchemy.schema import Table

from pyyaul.db import version


class Test_Version(TestCase):

    def setUp(self):
        class SchemaV0(version.Version):
            def _initMetaData(self, metadata):
                Table(
                    'widget',
                    metadata,
                    Column('id', Integer, primary_key=True),
                )

            def _update(self, engine):
                return engine

        self.clsSchemaV0 = SchemaV0

        class SchemaV1(version.Version):
            clsPrev = SchemaV0

            def _initMetaData(self, metadata):
                Table(
                    'widget',
                    metadata,
                    Column('id', Integer, primary_key=True),
                    Column('name', String(100)),
                )

            def _update(self, engine):
                self._updateAddColumn(
                    engine,
                    self.metadata.tables['widget'],
                    self.metadata.tables['widget'].columns['name'],
                )
                return engine

        self.clsSchemaV1 = SchemaV1

    def createEngine(self):
        return create_engine('sqlite:///:memory:')

    def getStoredVersion(self, clsVersion, engine):
        versionTable = clsVersion().get_version_table()
        with engine.connect() as connection:
            return connection.execute(
                select(versionTable.c.version).where(
                    versionTable.c.schema_class == clsVersion.get_schema_id()
                )
            ).scalar_one()

    def test_initialize_writes_schema_version(self):
        engine = self.createEngine()
        self.clsSchemaV0().update(engine)
        self.assertEqual(self.getStoredVersion(self.clsSchemaV0, engine), 0)
        self.assertTrue(
            inspect(engine).has_table(self.clsSchemaV0().get_version_table().name)
        )

    def test_version_fast_path_finds_previous_schema(self):
        engine = self.createEngine()
        self.clsSchemaV0().update(engine)
        self.assertIs(self.clsSchemaV1().version(engine), self.clsSchemaV0)

    def test_update_writes_new_schema_version(self):
        engine = self.createEngine()
        self.clsSchemaV0().update(engine)
        self.clsSchemaV1().update(engine)
        self.assertEqual(self.getStoredVersion(self.clsSchemaV1, engine), 1)
        self.assertIs(self.clsSchemaV1().version(engine), self.clsSchemaV1)
        widgetColumns = inspect(engine).get_columns('widget')
        self.assertEqual([column['name'] for column in widgetColumns], ['id', 'name'])

    def test_version_falls_back_when_version_table_is_missing(self):
        engine = self.createEngine()
        self.clsSchemaV1().metadata.create_all(engine)
        self.assertIs(self.clsSchemaV1().version(engine), self.clsSchemaV1)


if __name__ == '__main__':
    unittest.main()
