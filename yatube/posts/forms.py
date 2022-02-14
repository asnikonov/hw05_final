from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        help_texts = {
            'text': 'Текст вашего поста',
            'group': 'Выберите группу',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария'
        }
        help_texts = {
            'text': 'Текст вашего комментария',
        }
