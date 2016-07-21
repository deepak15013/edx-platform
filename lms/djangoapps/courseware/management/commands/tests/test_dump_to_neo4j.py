 # coding=utf-8

import mock

from courseware.management.commands.dump_to_neo4j import ModuleStoreSerializer
from django.core.management import call_command
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class TestDumpToNeo4jCommandBase(SharedModuleStoreTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestDumpToNeo4jCommandBase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.chapter = ItemFactory.create(parent=cls.course, category='chapter')
        cls.sequential = ItemFactory.create(parent=cls.chapter, category='sequential')
        cls.vertical = ItemFactory.create(parent=cls.sequential, category='vertical')
        cls.html = ItemFactory.create(parent=cls.vertical, category='html')
        cls.problem = ItemFactory.create(parent=cls.vertical, category='problem')
        cls.video = ItemFactory.create(parent=cls.vertical, category='video')
        cls.video2 = ItemFactory.create(parent=cls.vertical, category='video')

class TestDumpToNeo4jCommand(SharedModuleStoreTestCase):
    """
    Tests for the dump to neo4j management command
    """
    def setUp(self):
        super(TestDumpToNeo4jCommand, self).setUp()


    def test_dump_to_neo4j(self):
        with mock.patch('py2neo.Graph') as MockGraph:
            call_command('dump_to_neo4j')


class TestModuleStoreSerializer(TestDumpToNeo4jCommandBase):
    """
    Tests for the ModuleStoreSerializer
    """
    def setUp(self):
        super(TestModuleStoreSerializer, self).setUp()
        self.modulestore_serializer = ModuleStoreSerializer()

    def test_serialize_item(self):
        """
        Tests the _serialize_item method.
        """
        fields, label = self.modulestore_serializer._serialize_item(self.course)
        self.assertEqual(label, "course")
        self.assertIn("edited_on", fields.keys())
        self.assertIn("display_name", fields.keys())
        self.assertIn("org", fields.keys())
        self.assertIn("course", fields.keys())
        self.assertIn("run", fields.keys())
        self.assertIn("course_key", fields.keys())
        self.assertNotIn("checklist", fields.keys())

    def test_serialize_course(self):
        """
        Tests the serialize_course method.
        """

        nodes, relationships = self.modulestore_serializer.serialize_course(
            self.course.id
        )
        self.assertEqual(len(nodes), 9)
        self.assertEqual(len(relationships), 7)
