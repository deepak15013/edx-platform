import logging

from django.core.management.base import BaseCommand
from py2neo import Graph, Node, Relationship, authenticate, Subgraph
from py2neo.compat import integer, string, unicode
from request_cache.middleware import RequestCache
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

logger = logging.getLogger('neo4j.bolt')
logger.propagate = False
logger.disabled = True

ACCEPTABLE_TYPES = (integer, string, unicode, float, bool, tuple, list, set, frozenset)

class ModuleStoreSerializer(object):
    """
    Class with functionality to serialize a modulestore into subgraphs,
    one graph per course.
    """
    def __init__(self):
        self.all_courses = modulestore().get_course_summaries()

    @staticmethod
    def _serialize_item(item):
        """
        Args:
            item: an XBlock
            course_key: the course key of the course the item is in

        Returns:
            fields: a dictionary of an XBlock's field names and values
            label: the name of the XBlock's type (i.e. 'course'
            or 'problem')
        """
        # convert all fields to a dict and filter out parent and children field
        fields = dict(
            (field, field_value.read_from(item))
            for (field, field_value) in item.fields.iteritems()
            if field not in ['parent', 'children']
        )

        course_key = item.scope_ids.usage_id.course_key

        # set reset some defaults
        fields['edited_on'] = unicode(getattr(item, 'edited_on', u''))
        fields['display_name'] = item.display_name_with_default
        fields['org'] = course_key.org
        fields['course'] = course_key.course
        fields['run'] = course_key.run
        fields['course_key'] = unicode(course_key)

        label = item.scope_ids.block_type

        # prune some fields
        if label == 'course':
            if 'checklists' in fields:
                del fields['checklists']

        return fields, label

    def serialize_course(self, course_id):
        """
        Args:
            course_id: CourseKey of the course we want to serialize

        Returns:
            nodes: a list of py2neo Node objects
            relationships: a list of py2neo Relationships objects

        Takes serializes a course into Nodes and Relationships
        """
        # create a location to node mapping we'll need later for
        # writing relationships
        location_to_node = {}
        items = modulestore().get_items(course_id)
        nodes = []
        relationships = []

        for item in items:
            fields, label = self._serialize_item(item)

            for field_name, value in fields.iteritems():
                fields[field_name] = self.coerce_types(value)

            if label.__class__ not in ACCEPTABLE_TYPES:
                label = unicode(label)

            node = Node(label, **fields)
            nodes.append(node)
            location_to_node[item.location] = node

        for item in items:
            for child_loc in item.get_children():
                parent_node = location_to_node.get(item.location)
                child_node = location_to_node.get(child_loc.location)
                if parent_node is not None and child_node is not None:
                    relationship = Relationship(parent_node, "PARENT_OF", child_node)
                    relationships.append(relationship)

        return nodes, relationships

    @staticmethod
    def coerce_types(value):
        """
        Args:
            value: the value of an xblock's field

        Returns: either the value, a unicode version of the value, or, if the
        value is iterable, the value with each element being converted to unicode
        """
        if value.__class__ in (tuple, list, set, frozenset):
            for index, element in enumerate(value):
                value[index] = unicode(element)

        elif value.__class__ not in ACCEPTABLE_TYPES:
            value = unicode(value)

        return value


class Command(BaseCommand):
    """
    Command to dump modulestore data to neo4j
    """
    def handle(self, *args, **kwargs):

        mss = ModuleStoreSerializer()

        graph = Graph(password="edx", bolt=True)
        authenticate("localhost:7474", 'neo4j', 'edx')

        import ipdb; ipdb.set_trace()

        log.info("deleting existing coursegraph data")
        graph.delete_all()
        total_number_of_courses = len(mss.all_courses)

        for index, course in enumerate(mss.all_courses):
            # first, clear the request cache to prevent memory leaks
            RequestCache.clear_request_cache()

            log.info(
                u"Now dumping %s, course %d of %d",
                course.id,
                index + 1,
                total_number_of_courses
            )
            nodes, relationships = mss.serialize_course(course.id)
            transaction = graph.begin()

            try:
                for node in nodes:
                    transaction.create(node)

                for relationship in relationships:
                    transaction.create(relationship)

            except Exception:
                log.exception(
                    u"Error trying to dump course %s to neo4j, rolling back",
                    unicode(course.id)
                )
                transaction.rollback()

            transaction.commit()



