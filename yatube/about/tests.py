from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTests(TestCase):

    def test_about_author(self):
        """Страница author доступна любому пользователю."""
        response = Client().get(reverse('about:author'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_tech(self):
        """Страница tech доступна любому пользователю."""
        response = Client().get(reverse('about:tech'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
