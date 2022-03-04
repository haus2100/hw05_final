from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

from http import HTTPStatus

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

        cls.user = User.objects.create_user(username='user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.author = User.objects.create_user(username='author')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
            description='test_descrioption'
        )

        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=cls.author
        )

        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for adress, template in PostURLTest.templates_url_names.items():
            with self.subTest(adress=adress):
                response = PostURLTest.authorized_author.get(
                    adress, follow=True
                )
                self.assertTemplateUsed(response, template)

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_urls(self):
        """Проверка работы страниц"""
        urls = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
            '/create/',
            f'/posts/{self.post.id}/edit/',
        }
        for adress in urls:
            with self.subTest(adress=adress):
                response = PostURLTest.authorized_author.get(
                    adress, follow=True
                )
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_urls_guest(self):
        """Проверка работы страниц для  неавторизованного пользователя"""
        urls = {
            '/': HTTPStatus.OK.value,
            f'/group/{self.group.slug}/': HTTPStatus.OK.value,
            f'/profile/{self.user.username}/': HTTPStatus.OK.value,
            f'/posts/{self.post.id}/': HTTPStatus.OK.value,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
        }
        for adress, expected in urls.items():
            with self.subTest(adress=adress):
                response = PostURLTest.guest_client.get(
                    adress
                )
                self.assertEqual(response.status_code, expected)
