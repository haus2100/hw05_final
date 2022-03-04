from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
            description='test_descrioption',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_model_group_has_correct_object_names(self):
        group = PostModelTest.group
        expected_group_name = group.title
        self.assertEqual(expected_group_name, str(group))

    def test_model_post_has_correct_object_names(self):
        post = PostModelTest.post
        expected_post_name = post.text[:15]
        self.assertEqual(expected_post_name, str(post))
