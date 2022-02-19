import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
        )

        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_post_create(self):
        """Валидная форма создает запись в Posts."""
        posts_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'group': self.group.id,
            'text': 'Текст поста который будет проверен',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username':
                                                       self.post.author}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text=self.post.text,
                image=self.post.image,
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        post = self.post
        form_data = {'text': 'Текст обновленного поста', }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        post.refresh_from_db()
        expected = post.text
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post.id}))
        self.assertEqual(expected, 'Текст обновленного поста')

    def test_group_edit(self):
        """Валидная форма обновляет группу поста."""
        post = self.post
        form_data = {'text': self.post.text,
                     'group': self.group2.pk}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        post.refresh_from_db()
        expected = post.group.pk
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id}))
        self.assertEqual(expected, self.group2.pk)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст поста',
        )
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_create_user(self):
        """Проверяем создание комментария пользователем в БД."""
        count_comments = Comment.objects.count()

        form_data = {'text': 'Тестовый комментарий. Да начнется холивар!'}

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(Comment.objects.count(), count_comments + 1)

    def test_comment_create_guest(self):
        """Проверяем создание комментария гостем в БД."""
        count_comments = Comment.objects.count()

        form_data = {'text': 'Тестовый комментарий. Да начнется холивар!'}

        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, f'/auth/login/?next=/posts/'
                                       f'{self.post.id}/comment/')
        self.assertEqual(Comment.objects.count(), count_comments)

    def test_comment_create_context(self):
        """Валидная форма добавляет комментарий к выбранному посту."""
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Текст комментария')
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertIn(comment, response.context['comments'])
