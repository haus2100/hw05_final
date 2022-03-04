import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTest(TestCase):
    """
    Тестирование формы.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Заголовок для форм",
            slug="second",
            description="new_descr_form",
        )
        cls.small_png = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.png', content=cls.small_png, content_type="image/png"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.author = User.objects.create_user(username="Nick")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_form_create(self):
        """
        Валидная форма создает запись.
        """
        post_count = Post.objects.count()
        form_data = {
            "text": "new text form",
            "group": self.group.id,
            "image": self.uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )

        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.author}),
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data.get("text"),
                author=self.author,
                group=self.group,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """
        Валидная форма редактируется.
        """
        post = Post.objects.create(
            author=self.author,
            text="new text form",
            group=self.group,
            image=self.uploaded,
        )
        form_data = {
            "text": "changed text",
            "group": self.group.id,
            "image": post.image,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=[post.id]),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response, reverse("posts:post_detail", args=[post.id])
        )
        new_post = Post.objects.get(id=post.id)
        created_post = response.context.get("post")
        post.refresh_from_db()
        self.assertEqual(new_post.text, created_post.text)
        self.assertEqual(new_post.group, created_post.group)
        self.assertEqual(new_post.image, created_post.image)


class CommetnFormTest(TestCase):
    """
    Тестирование формы комментария.
    """

    def setUp(self) -> None:
        self.author = User.objects.create_user(username="Tester")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.group = Group.objects.create(
            title="comment-title",
            slug="third",
            description="new_descr_form_comm",
        )
        self.post = Post.objects.create(
            text="kekw-text", author=self.author, group=self.group
        )

    def test_comments(self):
        """
        Комментария появляется у поста.
        """

        count_comments = Comment.objects.count()
        form_data = {
            "text": "комментарий!",
        }
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), count_comments + 1)
        self.assertRedirects(
            response, reverse("posts:post_detail", args=[self.post.id])
        )
        new_comm = Comment.objects.get(pk=self.post.id)
        created_comm = response.context.get("comments")[0]
        self.assertEqual(new_comm.text, created_comm.text)
