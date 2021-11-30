from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea, DateTimeInput, DateTimeField, DateField, DateInput, CharField, ChoiceField, Field, BooleanField, HiddenInput, ModelMultipleChoiceField, CheckboxSelectMultiple
from bootstrap_modal_forms.forms import BSModalModelForm

class Tags(models.Model):
    tag = models.CharField(max_length=20)

    def __str__(self):
        return self.tag

class Advertisments(models.Model):
    text = models.CharField(null=False, blank=False, max_length=7000)
    image = models.ImageField(upload_to='adv_images/', null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.RESTRICT)
    tags = models.ManyToManyField(Tags, null=True, blank=True)
    expired_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.text[0:40]}...'

class CreateAdvertisment(ModelForm):
    text = CharField(widget=Textarea(attrs={'cols': 100, 'rows': 15}))
    tags = ModelMultipleChoiceField(queryset=Tags.objects.all(), widget=CheckboxSelectMultiple, required=False)
    expired_date = DateTimeField(input_formats=['%d/%m/%Y %H:%M'], required=False)
    model = Advertisments

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    #    self.initial['author'] = self.request.user

    def clean(self):
        cleaned_data = super().clean()
        self.instance.author = self.request.user
        return cleaned_data

    class Meta:
        model = Advertisments
        fields = '__all__'
        exclude = ['author']

