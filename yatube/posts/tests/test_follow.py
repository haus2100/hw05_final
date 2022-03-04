from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post, User


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create(
            username='test_username',
            email='testmail@gmail.com',
            password='Qwerty123',
        )
        cls.test_user_2 = User.objects.create(
            username='test_username_2',
            email='testmail_2@gmail.com',
            password='Qwerty123-2',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user_2)

    def test_authorized_client_can_follow_authors(self):
        """Авторизованный пользователь может подписаться на авторов."""
        follow_counts_before = Follow.objects.count()
        follow_url = reverse('posts:profile_follow',
                             args=[self.test_user.username])
        response = self.authorized_client.get(follow_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        follow_exists = Follow.objects.filter(
            user=self.test_user_2,
            author=self.test_user,
        ).exists()
        self.assertTrue(follow_exists)
        self.assertEqual(Follow.objects.count(), follow_counts_before + 1)

    def test_authorized_client_can_unfollow_authors(self):
        """Авторизованный пользователь может отписаться от авторов."""
        follow_counts_before = Follow.objects.count()
        Follow.objects.create(
            user=self.test_user_2,
            author=self.test_user,
        )
        unfollow_url = reverse('posts:profile_unfollow',
                               args=[self.test_user.username])
        response = self.authorized_client.get(unfollow_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        follow_exists = Follow.objects.filter(
            user=self.test_user_2,
            author=self.test_user,
        ).exists()
        self.assertFalse(follow_exists)
        self.assertEqual(Follow.objects.count(), follow_counts_before)

    def test_new_post_appears_for_followers(self):
        """Новая запись пользователя отображается в ленте тех,
        кто на него подписан."""
        Follow.objects.create(
            user=self.test_user_2,
            author=self.test_user,
        )
        post = Post.objects.create(
            author=self.test_user,
            text='Тестовый текст публикации',
        )
        follow_index_url = reverse('posts:follow_index')
        user_response = self.authorized_client.get(follow_index_url)
        user_content = user_response.context['page_obj']
        self.assertIn(post, user_content)

    def test_new_post_does_not_appear_for_nonfollowers(self):
        """Новая запись пользователя не отображается в ленте тех,
        кто на него не подписан."""
        post = Post.objects.create(
            author=self.test_user,
            text='Тестовый текст публикации',
        )
        follow_index_url = reverse('posts:follow_index')
        user_response = self.authorized_client.get(follow_index_url)
        user_content = user_response.context['page_obj']
        self.assertNotIn(post, user_content)
