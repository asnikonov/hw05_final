import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
            image=uploaded,
        )

        Post.objects.bulk_create(
            [
                Post(text=f'Текст поста {i}',
                     author=cls.user,
                     group=cls.group,
                     image=uploaded)
                for i in range(1, 5)
            ]
        )

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}): 'posts/create_post.html',
            reverse(
                'posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон 'index' сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        for post in response.context['page_obj']:
            some_post = Post.objects.get(id=post.id)
            values = {
                post.text: some_post.text,
                post.group: self.post.group,
                post.author: self.post.author,
            }
            for key, value in values.items():
                with self.subTest(key=key):
                    self.assertEqual(key, value)
            self.assertContains(response, 'image')

    def test_group_list_show_correct_context(self):
        """Шаблон 'group_list' сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:group_posts',
                                              kwargs={'slug':
                                                      self.group.slug})
                                              )
        for post in response.context['page_obj']:
            some_post = Post.objects.get(id=post.id)
            values = {
                post.text: some_post.text,
                post.group: self.post.group,
                post.author: self.post.author,
            }
            for key, value in values.items():
                with self.subTest(key=key):
                    self.assertEqual(key, value)
            self.assertContains(response, 'image')

    def test_profile_show_correct_context(self):
        """Шаблон 'profile' сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.post.author})
        )
        for post in response.context['page_obj']:
            some_post = Post.objects.get(id=post.id)
            values = {
                post.text: some_post.text,
                post.group.slug: self.post.group.slug,
                post.author: self.post.author,
            }
            for key, value in values.items():
                with self.subTest(key=key):
                    self.assertEqual(key, value)
            self.assertContains(response, 'image')

    def test_post_detail_correct_context(self):
        """Шаблон 'post_detail' сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk})
        )
        post_on_page = response.context['post']
        post_text = post_on_page.text
        post_group_slug = post_on_page.group.slug
        post_author = post_on_page.author
        values = {
            post_text: self.post.text,
            post_group_slug: self.post.group.slug,
            post_author: self.post.author,
        }
        for key, value in values.items():
            with self.subTest(key=key):
                self.assertEqual(key, value)
        self.assertContains(response, 'image')

    def test_post_edit_correct_context(self):
        """Шаблон 'post_edit' сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_correct_context(self):
        """Шаблон 'post_create' сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache_index_page_correct_context(self):
        """Кэш index сформирован с правильным контекстом."""
        first_response = self.authorized_client.get(reverse('posts:index'))
        old_content = first_response.content
        context = first_response.context['page_obj']
        self.assertIn(self.post, context)
        post = Post.objects.get(id=self.post.id)
        post.delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        new_content = second_response.content
        self.assertEqual(old_content, new_content)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        new_new_content = third_response.content
        self.assertNotEqual(old_content, new_new_content)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PaginatorViewsTest(TestCase):

    display_on_first_page = 10
    display_on_second_page = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
        )

        Post.objects.bulk_create(
            [
                Post(text="Тестовый текст", author=cls.user, group=cls.group)
                for i in range(1, 13)
            ]
        )

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)
        cache.clear()

    def test_index_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'].paginator.get_page(
            '1').object_list.count(), self.display_on_first_page)

    def test_index_second_page_contains_four_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(response.context['page_obj'].paginator.get_page(
            '2').object_list.count(), self.display_on_second_page)

    def test_group_list_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug':
                                                   'test-slug'}))
        self.assertEqual(response.context['page_obj'].paginator.get_page(
            '1').object_list.count(), self.display_on_first_page)

    def test_group_list_second_page_contains_four_records(self):
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug':
                                                   'test-slug'}) + '?page=2')
        self.assertEqual(response.context['page_obj'].paginator.get_page(
            '2').object_list.count(), self.display_on_second_page)

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username':
                                                   self.post.
                                                   author}))
        self.assertEqual(response.context['page_obj'].paginator.get_page(
            '1').object_list.count(), self.display_on_first_page)

    def test_profile_second_page_contains_four_records(self):
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username':
                                                   self.post.
                                                   author}) + '?page=2')
        self.assertEqual(response.context['page_obj'].paginator.get_page(
            '2').object_list.count(), self.display_on_second_page)


class AdditionalGroupPostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

        cache.clear()

    def test_pages_contains_test_group_post(self):
        """При создании поста с группой он появляется на всех страницах."""
        adresses = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': self.post.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author})
        ]
        for adress in adresses:
            response = self.client.get(adress)
            first_object = response.context['page_obj'][0]
            post_text = first_object.text
            post_group = first_object.group.title
            self.assertEqual(post_text, self.post.text)
            self.assertEqual(post_group, self.post.group.title)
