from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea, DateTimeInput, \
    DateTimeField, DateField, DateInput, CharField, ChoiceField, Field, \
    BooleanField, HiddenInput, ModelMultipleChoiceField, CheckboxSelectMultiple, FileField, ClearableFileInput, ImageField
from bootstrap_modal_forms.forms import BSModalModelForm
from django.utils.timezone import now

class Tags(models.Model):
    tag = models.CharField(max_length=20)

    def __str__(self):
        return self.tag

class Advertisments(models.Model):
    text = models.CharField(null=False, blank=False, max_length=7000)
    image = models.ImageField(upload_to='adv_images/', null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.RESTRICT)
    tags = models.ManyToManyField(Tags, blank=True)
    expired_date = models.DateTimeField(null=True, blank=True)
    release_date = models.DateTimeField(default=now().replace(microsecond=True))

    def __str__(self):
        return f'{self.text[0:40]}...'

class CreateAdvertisment(ModelForm):
    text = CharField(widget=Textarea(attrs={'cols': 100, 'rows': 15}))
    tags = ModelMultipleChoiceField(queryset=Tags.objects.all(), widget=CheckboxSelectMultiple, required=False)
    expired_date = DateTimeField(input_formats=['%d/%m/%Y %H:%M'], required=False)
    image = ImageField(widget=ClearableFileInput(attrs={'multiple': True}), required=False)
    model = Advertisments

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    #    self.initial['author'] = self.request.user

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('image')
        if form.is_valid():
            #for f in files:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def clean(self):
        cleaned_data = super().clean()
        self.instance.author = self.request.user
        return cleaned_data

    class Meta:
        model = Advertisments
        fields = '__all__'
        exclude = ['author']
        widgets = {
            'image': ClearableFileInput(attrs={'multiple': True})
        }
