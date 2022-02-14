from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()

POSTS_ON_PAGE = 10


@cache_page(20 * 1)
def index(request):
    main = 'Последние обновления на сайте'
    latest = Post.objects.select_related('group')
    paginator = Paginator(latest, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/index.html'
    context = {
        'text': main,
        'page_obj': page_obj,
        'index': True,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if (
        user.is_authenticated and author != request.user
        and Follow.objects.filter(author=author, user=request.user).exists()
    ):
        following = True
    else:
        following = False
    post_list = author.posts.all()
    paginator = Paginator(post_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/profile.html'
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    form = CommentForm()
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template_name = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        username = request.user.username
        return redirect('posts:profile', username)
    return render(request, template_name, {'form': form})


@login_required
def post_edit(request, post_id):
    template_name = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if post.author == request.user:
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post_id)
    else:
        return redirect('posts:post_detail', post_id)
    return render(request, template_name, {'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    text = 'Избранные авторы'
    name = request.user
    authors = name.follower.all().values('author')
    post_list = Post.objects.filter(author__in=authors)

    paginator = Paginator(post_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/follow.html'
    context = {
        'text': text,
        'page_obj': page_obj,
        'follow': True,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=user, author=author)
    if request.user != author and not following.exists():
        Follow.objects.create(user=request.user, author=author)
        return redirect('posts:profile', username=username)

    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=user).delete()
    return redirect('posts:profile', username=author)
