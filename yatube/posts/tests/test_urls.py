from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Group, Post
from django.urls import reverse
from http import HTTPStatus
from django.core.cache import cache


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст поста',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

        cache.clear()

    def test_homepage_guest(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_posts_guest(self):
        """Страница /group/<slug>/ доступна любому пользователю."""
        response = self.guest_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': 'test-slug'}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_guest(self):
        """Страница /profile/<username>/ доступна любому пользователю."""
        response = self.guest_client.get(reverse('posts:profile',
                                                 kwargs={'username':
                                                         self.user}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_guest(self):
        """Страница /posts/<post_id>/ доступна любому пользователю."""
        response = self.guest_client.get(reverse('posts:post_detail',
                                                 kwargs={'post_id':
                                                         self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_author(self):
        """Страница /posts/<post_id>/edit доступна автору."""
        response = self.author_client.get(reverse('posts:post_edit',
                                                  kwargs={'post_id':
                                                          self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_user(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_redirect_guest(self):
        """Страница /posts/<post_id>/edit редиректит анонимного пользователя"""
        response = self.guest_client.get(reverse('posts:post_edit',
                                                 kwargs={'post_id':
                                                         self.post.id}),
                                         follow=True)
        self.assertRedirects(response, f'/auth/login/?next=/posts/'
                                       f'{self.post.id}/edit/')

    def test_post_edit_redirect_user(self):
        """Страница /posts/<post_id>/edit редиректит не автора."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id':
                                                              self.post.id}))
        self.assertRedirects(response, (reverse('posts:post_detail',
                                                kwargs={'post_id':
                                                        self.post.id})))

    def test_post_create_redirect_guest(self):
        """Страница /posts/create/ редиректит анонимного пользователя. """
        response = self.guest_client.get(reverse('posts:post_create'),
                                         follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_unexisting_page(self):
        """Запрос к страница unexisting_page вернет ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            (reverse('posts:index')): 'posts/index.html',
            (reverse('posts:group_posts',
                     kwargs={'slug':
                             'test-slug'})): 'posts/group_list.html',
            (reverse('posts:profile',
                     kwargs={'username':
                             self.user})): 'posts/profile.html',
            (reverse('posts:post_detail',
                     kwargs={'post_id':
                             self.post.id})): 'posts/post_detail.html',
            (reverse('posts:post_edit',
                     kwargs={'post_id':
                             self.post.id})): 'posts/create_post.html',
            (reverse('posts:post_create')): 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
