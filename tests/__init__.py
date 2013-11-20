import unittest

from peewee import SqliteDatabase

from arnold import (
    _perform_migrations, _perform_single_migration, _setup_table, main
)
from arnold.exceptions import (
    DBAttrNotFound,
    FieldNotFoundException,
    FieldsRequiredException,
    InvalidConfiguration,
    ModuleNotFoundException
)
from arnold.models import Migration
from arnold.peewee_helpers import create_table


db = SqliteDatabase('test.db')

directory = "tests/migrations"
migration_module = "tests.migrations"

kwargs = {
    'directory': directory,
    'migration_module': migration_module
}


class TestMigrationFunctions(unittest.TestCase):
    def setUp(self):
        self.model = Migration
        self.model._meta.database = db
        self.model.create_table()

        self.good_migration = "001_initial"
        self.bad_migration = "bad"

    def tearDown(self):
        self.model.drop_table()

    def test_setup_table(self):
        """Ensure that the Migration table will be setup properly"""
        # Drop the table if it exists, as we are creating it later
        if self.model.table_exists():
            self.model.drop_table()

        self.assertTrue(_setup_table(self.model))
        self.assertTrue(_setup_table(self.model) is None)

    def do_good_migration_up(self):
        """A utility to perform a successfull upwards migration"""
        self.assertTrue(_perform_single_migration(
            "up", self.model, migration=self.good_migration, **kwargs
        ))

    def do_good_migration_down(self):
        """A utility to perform a successfull downwards migration"""
        self.assertTrue(_perform_single_migration(
            "down", self.model, migration=self.good_migration, **kwargs
        ))

    def test_perform_single_migration(self):
        """A simple test of _perform_single_migration"""
        self.do_good_migration_up()

    def test_perform_single_migration_already_migrated(self):
        """Run migration twice, second time should return False"""
        self.do_good_migration_up()

        self.assertFalse(_perform_single_migration(
            "up", self.model, migration=self.good_migration, **kwargs
        ))

    def test_perform_single_migration_not_found(self):
        """Ensure that a bad migration argument raises an error"""
        with self.assertRaises(ModuleNotFoundException):
            _perform_single_migration(
                "up", self.model, migration=self.bad_migration, **kwargs
            )

    def test_perform_single_migration_down(self):
        """A simple test of _perform_single_migration down"""
        self.do_good_migration_up()

        self.do_good_migration_down()

    def test_perform_single_migration_down_does_not_exist(self):
        """Ensure False response when migration isn't there"""
        self.assertFalse(_perform_single_migration(
            "down", self.model, migration=self.good_migration, **kwargs
        ))

    def test_perform_single_migration_adds_deletes_row(self):
        """Make sure that the migration rows are added/deleted"""
        self.do_good_migration_up()

        self.assertTrue(self.model.select().where(
            self.model.migration == self.good_migration
        ).limit(1).exists())

        self.do_good_migration_down()

        self.assertFalse(self.model.select().where(
            self.model.migration == self.good_migration
        ).limit(1).exists())

    def test_perform_migrations(self):
        """A simple test of _perform_migrations"""
        self.assertEqual(_perform_migrations(
            "up", self.model, **kwargs
        ), True)

    def test_perform_migrations_with_migration_argument(self):
        """A simple test of _perform_migrations with a migration argument"""
        self.assertTrue(_perform_migrations(
            "up", self.model, migration=self.good_migration, **kwargs
        ))

    def test_main_single_migration(self):
        """Call arnold's main method and perform a single migration"""
        self.assertTrue(main(database=db, **kwargs))

    def test_main_ignore_migration(self):
        """If we pass files to ignore, make sure they aren't run"""
        self.assertTrue(main(database=db, ignored=["001_initial"], **kwargs))
        self.assertFalse(self.model.select().where(
            self.model.migration == self.good_migration
        ).limit(1).exists())

    def test_main_no_database_raise_error(self):
        """If we don't pass a database in, raise an error"""
        with self.assertRaises(DBAttrNotFound):
            main(**kwargs)

    def test_no_directory_or_module_raises_error(self):
        """If we don't pass directory or module, raise an error"""
        # Try without directory first
        with self.assertRaises(InvalidConfiguration):
            main(database=db, migration_module=migration_module)

        # Try without module
        with self.assertRaises(InvalidConfiguration):
            main(database=db, directory=directory)


class TestUtilMethods(unittest.TestCase):
    def setUp(self):
        self.model = Migration
        self.model._meta.database = db

    def tearDown(self):
        if self.model.table_exists():
            self.model.drop_table()

    def test_create_table(self):
        create_table(self.model, ["id", "migration"])
        self.assertTrue(self.model.table_exists())

    def test_create_table_fails_on_unkown_field(self):
        with self.assertRaises(FieldNotFoundException):
            create_table(self.model, ["id", "migration", "bad_field"])

    def test_create_table_with_empty_fields_raises_exception(self):
        with self.assertRaises(FieldsRequiredException):
            create_table(self.model, [])

if __name__ == '__main__':
    unittest.main()
