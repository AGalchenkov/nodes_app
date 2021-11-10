from django.db import models
from django.forms import ModelForm, Textarea, CharField, ChoiceField, Field
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import time, datetime
from django.utils.timezone import now

class Customers(models.Model):
    customer = models.CharField(unique=True, max_length=50)
    def __str__(self):
        return self.customer

class Locations(models.Model):
    rack_location = models.CharField(unique=True, max_length=50)
    def __str__(self):
        return self.rack_location

class Racks(models.Model):
    location = models.ForeignKey(Locations, on_delete=models.RESTRICT)
    rack_id = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1000),
        ],
        default=999
    )
    units_num = models.IntegerField(
        validators=[
            MinValueValidator(0, message='negative unit number'),
            MaxValueValidator(48, message='to much unit number'),
        ]
    )
    def __str__(self):
        return f'{self.location}_#{self.rack_id} ({self.units_num}U)'

class Models(models.Model):
    model_name = models.CharField(unique=True, max_length=20)
    units_takes = models.IntegerField(default=1,
        validators=[
            MinValueValidator(1, message='negative unit number'),
            MaxValueValidator(5, message='to much unit number'),
        ]
    )
    def __str__(self):
        return self.model_name


class Units(models.Model):
    in_use = models.BooleanField(default=False)
    used_by_other_unit = models.BooleanField(default=False)
    owner = models.ForeignKey(Customers, null=True, blank=True, default='', on_delete=models.SET_DEFAULT)
    rack = models.ForeignKey(Racks, on_delete=models.CASCADE)
  #  comment = models.OneToOneField(Comments, null=True, blank=True, default='', on_delete=models.SET_DEFAULT)
    model = models.ForeignKey(Models, null=True, blank=True, on_delete=models.RESTRICT)
    mng_ip = models.GenericIPAddressField(blank=True, null=True)
    sn = models.CharField(blank=True, max_length=30)
    unit_num = models.IntegerField(blank=False,
        validators=[
            MinValueValidator(0, message='negative unit number'),
            MaxValueValidator(48, message='to much unit number')
        ]
    )
    hostname = models.CharField(blank=True, max_length=15)
    release_date = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(editable=False, default=now().replace(microsecond=0))
    modified = models.DateTimeField(default=now().replace(microsecond=0))

    class Meta:
        unique_together = ['rack_id', 'unit_num']

    def __str__(self):
        return f'{self.rack.location}_{self.rack.id}#{self.model}#{self.unit_num}U'

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = now().replace(microsecond=0)
        self.modified = now().replace(microsecond=0)
        return super(Units, self).save(*args, **kwargs)

class Comments(models.Model):
    unit = models.OneToOneField(Units, null=True, blank=True, default='', on_delete=models.SET_DEFAULT)
    author = models.OneToOneField(Customers, null=True, blank=True, on_delete=models.CASCADE)
    text = models.CharField(max_length=1000, blank=True)
    pub_date = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.text


class UnitForm(ModelForm):
    error_css_class = 'error'
    rack = Field(disabled=True)
    modified = Field(disabled=True)
    unit_num = CharField(disabled=True)
    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3}), required=False)
    comment_owner = CharField(disabled=True, required=False)
    model = Units
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['rack'] = kwargs['instance'].rack
        print(self.initial)
        try:
            self.initial['comment'] = kwargs['instance'].comments
        except models.ObjectDoesNotExist:
            self.initial['comment'] = ''

    def clean(self):
        cleaned_data = super().clean()
        in_use = cleaned_data.get('in_use')
        owner = cleaned_data.get('owner')
        sn = cleaned_data.get('sn')
        unit_num = cleaned_data.get('unit_num')
        rack = cleaned_data.get('rack')
        model = cleaned_data.get('model')

        if in_use == True and owner == None:
            raise ValidationError('assigned(in use) unit must have owner')
        if sn or model:
            if model == None or sn == '':
                raise ValidationError('if one of fields model or SN are exist then both must be filled')
            sn_unit = Units.objects.filter(sn=sn).exclude(unit_num=unit_num, rack=rack)
            if sn_unit:
                raise ValidationError(f'unit with this SN are exists ({sn_unit[0]})')
        if in_use == False and owner:
            raise ValidationError('not in use unit must have no owner')
        if model and model.units_takes > 1:
            start_unit = int(unit_num) + 1
            end_unit = int(unit_num) + int(model.units_takes)
            list = [i for i in range(start_unit, end_unit)]
            for item in list:
                try:
                    u = Units.objects.get(rack=rack, unit_num=item)
                    if u.model or u.in_use == True:
                        raise ValidationError(f'for this model needs {model.units_takes}U next unit are in use')
                except ObjectDoesNotExist:
                    continue

        return self.cleaned_data

    class Meta:
        model = Units
        fields = '__all__'
        exclude = ['used_by_other_unit']

class CommentForm(ModelForm):
    class Meta:
        model = Comments
        fields = '__all__'

class UnitCreateForm(ModelForm):
    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3}), required=False)
    rack = Field(disabled=True)
    unit_num = Field(disabled=True)
    modified = Field(disabled=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['modified'] = now().replace(microsecond=0)

    class Meta:
        model = Units
        fields = '__all__'
        exclude = ['used_by_other_unit']

