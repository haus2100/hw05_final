from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Follow, Group, Post
from .forms import PostForm, CommentForm

User = get_user_model()


def get_page_context(queryset, request):
    paginator = Paginator(queryset, settings.FILL)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    posts = Post.objects.all()
    context = get_page_context(posts, request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    posts = group.group_posts.all()
    context = {
        'group': group,
    }
    context.update(get_page_context(posts, request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    context = {
        'author': author,
        'posts': posts,
    }
    context.update(get_page_context(posts, request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comment_form = CommentForm(request.POST or None)
    comments = post.comments.all()
    post_count = post.author.posts.all().count()
    title = f'Пост {post.text[:30]}'
    context = {
        'title': title,
        'post_count': post_count,
        'post': post,
        'comment_form': comment_form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid() and post.author == request.user:
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, 'posts/create_post.html', context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

@login_required
def follow_index(request):
    """
    Вью подписки.
    """

    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, settings.FILL)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj}
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    """
    Подписка на других авторов.
    """

    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(author=author, user=request.user)
    return redirect("posts:profile", request.user)


@login_required
def profile_unfollow(request, username):
    """
    Дизлайк/отписка от других авторов.
    """

    author = get_object_or_404(User, username=username)
    follow_obj = Follow.objects.filter(author=author, user=request.user)
    if follow_obj.exists:
        follow_obj.delete()
    return redirect("posts:profile", request.user)
