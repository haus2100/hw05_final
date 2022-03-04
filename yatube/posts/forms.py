from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'текст',
            'group': 'группа'
        }
        help_texts = {
            'text': 'все что угодно',
            'group': 'из муществующих'
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        lables = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        if len(text) > 1:
            return text
        raise forms.ValidationError("Не заполнен текст комментария!")
