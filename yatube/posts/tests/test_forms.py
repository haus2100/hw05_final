import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group',
            description='Тестовое описание',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.test_user = User.objects.create(
            username='test_username',
            email='testmail@gmail.com',
            password='Qwerty123',)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)

    def test_create_post(self):
        """Отправка валидной формы создаёт публикацию."""
        posts_before = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'author': self.test_user,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_before + 1)
        post = Post.objects.first() 
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, form_data['author'])


    def test_edit_post(self):
        """Отправка валидной формы редактирует публикацию."""
        post = Post.objects.create(
            group=self.group,
            text='Тестовый текст',
            author=self.test_user,
        )
        posts_count = Post.objects.count()
        edited_text = 'Отредактированный тестовый текст'
        form_data = {
            'group': self.group.id,
            'text': edited_text,
            'author': self.authorized_client,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id, }),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)
        edited_post = Post.objects.get(id=post.id)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])

    def test_guest_client_could_not_create_posts(self):
        """Проверка невозможности создания поста неавторизованным
        пользователем."""
        posts_before = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'author': self.guest_client,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        expected_redirect = str(reverse('users:login') + '?next='
                                + reverse('posts:post_create'))
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_before)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create(
            username='test_username',
            email='testmail@gmail.com',
            password='Qwerty123',
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.test_user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.test_user,
            group=cls.group,
            text='Тестовый текст',
        )

    def test_authorized_client_can_create_comments(self):
        """Авторизованный пользователь может комментировать посты."""
        comments_before = self.post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий к посту',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id, }),
            data=form_data,
            follow=True,
        )
        self.assertEqual(self.post.comments.count(), comments_before + 1)
        last_comment = self.post.comments.last()
        self.assertEqual(last_comment.text, form_data['text'])

    def test_guest_client_could_not_create_comments(self):
        """Неавторизованный пользователь не может комментировать посты."""
        comments_before = self.post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий к посту',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id, }),
            data=form_data,
            follow=True,
        )
        expected_redirect = str(reverse('users:login') + '?next='
                                + reverse('posts:add_comment',
                                          kwargs={'post_id': self.post.id, }))
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(self.post.comments.count(), comments_before)
