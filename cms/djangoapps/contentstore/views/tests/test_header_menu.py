#-*- coding: utf-8 -*-

"""
Course Header Menu Tests.
"""
from django.conf import settings
from django.test.utils import override_settings

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from util.testing import UrlResetMixin
from util.url import reload_django_url_config

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True


@override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
class TestHeaderMenu(CourseTestCase, UrlResetMixin):
    """
    Unit tests for the course header menu.
    """
    def setUp(self):
        """
        Set up the for the course header menu tests.
        """
        # Overriding the FEATURES_WITH_CERTS_ENABLED settings value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because  of the UrlResetMixin)
        super(TestHeaderMenu, self).setUp()
        self.reset_urls()

    def test_header_menu_without_web_certs_enabled(self):
        """
        Tests course header menu should not have `Certificates` menu item
        if course has not web/HTML certificates enabled.
        """
        reload_django_url_config()
        outline_url = reverse_course_url('course_handler', self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='text/html')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, '<li class="nav-item nav-course-settings-certificates">')

    def test_header_menu_with_web_certs_enabled(self):
        """
        Tests course header menu should have `Certificates` menu item
        if course has web/HTML certificates enabled.
        """
        self.course.cert_html_view_enabled = True
        self.save_course()
        reload_django_url_config()
        outline_url = reverse_course_url('course_handler', self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='text/html')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<li class="nav-item nav-course-settings-certificates">')
