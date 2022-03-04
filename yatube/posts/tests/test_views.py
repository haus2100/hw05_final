from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Group, Post

from yatube.settings import FILL

User = get_user_model()


class PostViewsTest(TestCase):
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

        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=[PostViewsTest.group.slug]):
            'posts/group_list.html',
            reverse('posts:profile',
                    args=[PostViewsTest.user.username]):
            'posts/profile.html',
            reverse('posts:post_detail', args=[PostViewsTest.post.id]):
            'posts/post_detail.html',
            reverse('posts:post_edit', args=[PostViewsTest.post.id]):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

    def test_uses_correct_template(self):
        """URL адресс использует соответствующий шаблон"""
        for reverse_name, template in (
            PostViewsTest.templates_pages_names.items()
        ):
            with self.subTest(reverse_name=reverse_name):
                response = PostViewsTest.authorized_author.get(
                    reverse_name, follow=True
                )
                self.assertTemplateUsed(response, template)

    def check(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.author)

    def test_index_show_correct_context(self):
        """Главная страница сформирована с правильным контекстом"""
        response = PostViewsTest.authorized_client.get(
            reverse('posts:index')
        )
        post = response.context['page_obj'][0]
        self.check(post)

    def test_group_list_correct_context(self):
        """Cтраница группы сформирована с правильным контекстом"""
        response = PostViewsTest.authorized_client.get(
            reverse('posts:group_list', args=[self.group.slug])
        )
        post = response.context['page_obj'][0]
        self.check(post)

    def test_post_profile_show_correct_context(self):
        """Страница профиля сформирована с правильным контекстом"""
        response = PostViewsTest.authorized_author.get(
            reverse('posts:profile', args=['author'])
        )
        post = response.context['page_obj'][0]
        self.check(post)

    def test_post_detail_show_correct_context(self):
        """Страница поста сформирована с правильным контекстом"""
        response = PostViewsTest.authorized_author.get(
            reverse('posts:post_detail', args=[1])
        )
        post = response.context['post']
        self.check(post)

    def test_post_create_show_correct_context(self):
        """Страница создания поста сформирована с правильным контекстом"""
        response = PostViewsTest.authorized_author.get(
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

    def test_post_edit_show_correct_context(self):
        """Страница создания поста сформирована с правильным контекстом"""
        response = PostViewsTest.authorized_author.get(
            reverse('posts:post_edit', args=[1])
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_shows_on_pages(self):
        """Проверяем, что новый пост показывается на нужных страницах"""

        self.new_group = Group.objects.create(
            title='new_group',
            slug='new_slug',
            description='something',
        )

        self.new_post = Post.objects.create(
            text='Новый текст',
            group=self.new_group,
            author=self.author,
        )

        form_data = {
            'text': 'Новый текст',
            'group': 'new_group',
        }
        response = self.authorized_author.post(
            reverse('posts:index'),
            data=form_data,
        )
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, form_data['text'])

        response = self.authorized_author.post(
            reverse('posts:group_list', args=['new_group']),
            data=form_data,
        )
        self.assertEqual(first_post.text, form_data['text'])

        response = self.authorized_author.post(
            reverse('posts:profile', args=[self.author]),
            data=form_data,
        )
        self.assertEqual(first_post.text, form_data['text'])

        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.group.slug])
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, self.post.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create(
            username='test_username',
            email='testmail@gmail.com',
            password='Qwerty123',
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.test_user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.bulk_create([
            Post(
                author=cls.test_user,
                group=cls.group,
                text=f'Тестовый текст поста номер {item}',
            )
            for item in range(13)
        ])

    def test_paginator_for_index_profile_group(self):
        """Паджинатор на страницах index, profile, group работает корректно."""
        first_page_len = FILL
        second_page_len = Post.objects.count() - FILL
        context = {
            reverse('posts:index'): first_page_len,
            reverse('posts:index') + '?page=2': second_page_len,
            reverse('posts:group_list', args=[PaginatorViewsTest.group.slug]):
            first_page_len,
            reverse('posts:group_list', args=[PaginatorViewsTest.group.slug])
            + '?page=2': second_page_len,
            reverse('posts:profile',
                    args=[PaginatorViewsTest.test_user.username]):
            first_page_len,
            reverse('posts:profile',
                    args=[PaginatorViewsTest.test_user.username]) + '?page=2':
            second_page_len,
        }
        for requested_page, page_len in context.items():
            with self.subTest(requested_page=requested_page):
                response = self.authorized_client.get(requested_page)
                self.assertEqual(len(response.context['page_obj']), page_len)
