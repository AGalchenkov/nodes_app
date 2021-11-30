from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea, CharField, ChoiceField, Field, BooleanField, HiddenInput
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import time, datetime
import ipaddress
from django.utils.timezone import now
from bootstrap_modal_forms.forms import BSModalModelForm

from ping3 import ping

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

class Vendors(models.Model):
    vendor_name = models.CharField(unique=True, max_length=20)
    def __str__(self):
        return self.vendor_name

class PowerSupply(models.Model):
    power = models.CharField(unique=True, max_length=2)
    def __str__(self):
        return self.power

class VendorModels(models.Model):
    vendor_model = models.CharField(unique=True, max_length=20)
    def __str__(self):
        return self.vendor_model

    class Meta:
        ordering = ('vendor_model',)

class Consoles(models.Model):
    console = models.CharField(unique=True, max_length=5)
    def __str__(self):
        return self.console


class Comments(models.Model):
    #unit = models.OneToOneField(Units, null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    text = models.CharField(max_length=1000, blank=True, null=True)
    #pub_date = models.DateTimeField(default=now().replace(microsecond=0))
    pub_date = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        if self.text == None:
            return ''
        return self.text

    def save(self, *args, **kwargs):
        if self.text:
            self.pub_date = now().replace(microsecond=0)
        return super(Comments, self).save(*args, **kwargs)

class Appliances(models.Model):
    appliance = models.CharField(unique=True, max_length=60)
    ram = models.IntegerField(null=True, blank=True,
        validators=[
            MinValueValidator(1, message='negative unit number'),
            MaxValueValidator(4096, message='to much unit number'),
        ]
    )
    ipmi = models.BooleanField(default=False)


    def __str__(self):
        return self.appliance


class Units(models.Model):
    in_use = models.BooleanField(default=False)
    used_by_unit = models.CharField(blank=True, default='', max_length=3)
    owner = models.ForeignKey(User, null=True, blank=True, default=None, related_name='owner', on_delete=models.SET_DEFAULT)
    rack = models.ForeignKey(Racks, null=True, blank=True, default=None,  on_delete=models.CASCADE)
    unit_num = models.IntegerField(blank=False,
        validators=[
            MinValueValidator(0, message='negative unit number'),
            MaxValueValidator(48, message='to much unit number')
        ]
    )
    model = models.ForeignKey(Models, null=True, blank=True, on_delete=models.RESTRICT)
    vendor = models.ForeignKey(Vendors,null=True, blank=True, on_delete=models.RESTRICT)
    power = models.ForeignKey(PowerSupply,null=True, blank=True, on_delete=models.RESTRICT)
    vendor_model = models.ForeignKey(VendorModels,null=True, blank=True, on_delete=models.RESTRICT)
    console = models.ForeignKey(Consoles,null=True, blank=True, on_delete=models.RESTRICT)
    mng_ip = models.GenericIPAddressField(blank=True, null=True)
    appliance = models.ForeignKey(Appliances, null=True, blank=True, default=None,  on_delete=models.RESTRICT)
    is_avaliable = models.BooleanField(default=False)
    sn = models.CharField(blank=True, max_length=30)
    hostname = models.CharField(blank=True, max_length=15)
    release_date = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(editable=False, default=now().replace(microsecond=0))
    modified = models.DateTimeField(default=now().replace(microsecond=0))
    modified_by = models.ForeignKey(User, null=True, blank=True, default=None, related_name='modified_by', on_delete=models.SET_DEFAULT)
    comment = models.OneToOneField(Comments, null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)

    class Meta:
        unique_together = ['rack_id', 'unit_num']

    def __str__(self):
        return f'{self.rack.location}_{self.rack.rack_id}#{self.model}#{self.unit_num}U'

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = now().replace(microsecond=0)
        #self.modified = now().replace(microsecond=0)
        return super(Units, self).save(*args, **kwargs)

#class Comments(models.Model):
#    unit = models.OneToOneField(Units, null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
#    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
#    text = models.CharField(max_length=1000, blank=True)
#    pub_date = models.DateTimeField(auto_now=True)
#    def __str__(self):
#        return self.text


class UnitForm(ModelForm):
    error_css_class = 'error'
    rack = Field(disabled=True)
    modified = Field(disabled=True)
    unit_num = CharField(disabled=True)
    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3}), required=False)
    comment_author = CharField(disabled=True, required=False)
    comment_pub_date = CharField(disabled=True, required=False)
    modified_by = CharField(disabled=True, required=False)
    ram = CharField(required=False, disabled=True)
    field_order = [
        'in_use', 'owner', 'rack', 'unit_num', 'model', 'vendor', 'power', 'vendor_model',
        'console', 'mng_ip', 'appliance', 'sn', 'ram', 'hostname', 'modified', 'modified_by', 'comment',
        'comment_author', 'comment_pub_date',
    ]
    model = Units
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.initial['rack'] = kwargs['instance'].rack
        try:
            self.initial['ram'] = kwargs['instance'].appliance.ram
        except AttributeError:
            self.initial['ram'] = None
        try:
            self.initial['comment_author'] = kwargs['instance'].comment.author
            self.initial['comment_pub_date'] = kwargs['instance'].comment.pub_date
        except AttributeError:
            self.initial['comment_author'] = None

    def add_fatboy(self, unit_num, model, rack):
        other_unit_used_list = []
        start_unit = int(unit_num) - 1
        end_unit = int(unit_num) - int(model.units_takes)
        if start_unit == 0 or end_unit < 0:
            raise ValidationError('At this unit cant set this model')
        list = [i for i in range(start_unit, end_unit, -1)]
        for item in list:
            try:
                u = Units.objects.get(rack=rack, unit_num=item)
                if u.model or u.in_use == True:
                    raise ValidationError(f'for this model needs {model.units_takes}U next unit are in use(U{u.unit_num})')
                else:
                    use_u = Units.objects.get(rack=rack, unit_num=item)
                    use_u.used_by_unit = unit_num
                    other_unit_used_list.append(use_u)
                    continue
            except ObjectDoesNotExist:
                raise ValidationError('Internal Error!!! Ask for administrator!')
        Units.objects.bulk_update(other_unit_used_list, ['used_by_unit'])

    def remove_fatboy(self, unit_num, old_model, rack):
        start_unit = int(unit_num) - 1
        end_unit = int(unit_num) - int(old_model.units_takes)
        list = [i for i in range(start_unit, end_unit, -1)]
        for item in list:
            use_u = Units.objects.get(rack=rack, unit_num=item)
            use_u.used_by_unit = ''
            use_u.save()
            continue

    def change_fatboy(self, unit_num, model, old_model, rack):
        start_unit = int(unit_num) - 1
        end_unit = int(unit_num) - int(old_model.units_takes)
        if model.units_takes > old_model.units_takes:
            diff = model.units_takes - old_model.units_takes
        else:
            diff = old_model.units_takes - model.units_takes
            list = [i for i in range(end_unit + 1, end_unit + diff + 1)]
            for item in list:
                use_u = Units.objects.get(rack=rack, unit_num=item)
                use_u.used_by_unit = ''
                use_u.save()
                continue

    def clean(self):
        print(f'########## CHANGED:   {self.changed_data}')
        print('SELF FORMS::::')
        print(self.instance.is_avaliable)
        other_unit_used_list = []
        user = self.request.user
        cleaned_data = super().clean()
        modified_by = cleaned_data.get('modified_by')
        comment = cleaned_data.get('comment')
        if not comment:
            cleaned_data['comment'] = None
            cleaned_data['comment_pub_date'] = None
        if comment in self.changed_data:
            cleaned_data['comment'] = Units.objects.get(id=comment).comment
        if 'mng_ip' in self.changed_data:
            mng_ip = cleaned_data.get('mng_ip')
            try:
                if ping(mng_ip, timeout=0.5):
                    self.instance.is_avaliable = True
                else:
                    self.instance.is_avaliable = False
            except (OSError, TypeError):
                self.instance.is_avaliable = False
        if not modified_by:
            cleaned_data['modified_by'] = None
        if self.has_changed():
            cleaned_data['modified_by'] = user
            cleaned_data['modified'] = now().replace(microsecond=0)
        else:
            cleaned_data['modified_by'] = User.objects.get(id=modified_by)
        in_use = cleaned_data.get('in_use')
        owner = cleaned_data.get('owner')
        sn = cleaned_data.get('sn')
        unit_num = cleaned_data.get('unit_num')
        rack = cleaned_data.get('rack')
        model = cleaned_data.get('model')
        vendor = cleaned_data.get('vendor')
        power = cleaned_data.get('power')
        #cleaned_data['modified_by'] = user
        old_model = Units.objects.get(rack=rack, unit_num=unit_num).model
        old_model_units_takes = old_model.units_takes if hasattr(old_model, 'units_takes') else 0

        if in_use == True and owner == None:
            raise ValidationError('assigned(in use) unit must have owner')
        if model:
            if sn == '':
                raise ValidationError('if one of fields model or SN are set then both must be filled')
            if vendor == None or power == None:
                raise ValidationError('if model are set then vendor and power must be filled')
        if sn:
            if model == None:
                raise ValidationError('if one of fields model or SN are set then both must be filled')
            sn_unit = Units.objects.filter(sn=sn).exclude(unit_num=unit_num, rack=rack)
            if sn_unit:
                raise ValidationError(f'unit with this SN are exists ({sn_unit[0]})')
        if in_use == False and owner:
            raise ValidationError('not in use unit must have no owner')
        if model:
            if old_model == model:
                pass
            else:
                if model.units_takes > 1 and old_model_units_takes > 1 and model.units_takes < old_model_units_takes:
                    self.change_fatboy(unit_num, model, old_model, rack)
               # elif model.units_takes > 1 and old_model_units_takes > 1 and model.units_takes > old_model_units_takes:
               #     pass
                elif model.units_takes > 1 and old_model == None or \
                        model.units_takes > 1 and old_model_units_takes > 1 and model.units_takes > old_model_units_takes or \
                        model.units_takes > 1 and old_model_units_takes == 1:
                    self.add_fatboy(unit_num, model, rack)
                elif model.units_takes == 1 and old_model_units_takes > 1 or model == None and old_model_units_takes > 1:
                    self.remove_fatboy(unit_num, old_model, rack)

        return self.cleaned_data

    class Meta:
        model = Units
        fields = '__all__'
        exclude = ['used_by_unit', 'comment', 'is_avaliable']

class CommentForm(ModelForm):
    class Meta:
        model = Comments
        fields = '__all__'


class SearchForm(ModelForm):

    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3}), required=False)
    has_model_choises = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )
    is_avaliable_choises = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )
    has_model = ChoiceField(choices=has_model_choises)
    is_avaliable = ChoiceField(choices=is_avaliable_choises)

    model = Units

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Units
        exclude = ['used_by_unit', 'in_use', 'unit_num', 'console', 'modified', 'modified_by']

class CSVForm(ModelForm):

    has_model_choises = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )
    is_avaliable_choises = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )

    model = Units

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Units
        exclude = ['used_by_unit', 'in_use', 'unit_num', 'console', 'modified', 'modified_by']



class UnitCreateForm(ModelForm):
    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3}), required=False)
    rack = Field(disabled=True)
    unit_num = Field(disabled=True)
    modified = Field(disabled=True)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.initial['modified'] = now().replace(microsecond=0)


    class Meta:
        model = Units
        fields = '__all__'
        exclude = ['used_by_other_unit']

class BsUnitForm(BSModalModelForm):
    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3}), required=False, disabled=True)
    sn = Field(disabled=True)
    appliance = Field(disabled=True)
    power = Field(disabled=True)
    vendor = Field(disabled=True)
    model = Field(disabled=True)
    vendor_model = Field(disabled=True)
    ram = Field(disabled=True)
    field_order = ['model', 'vendor', 'vendor_model', 'power', 'appliance', 'ram', 'sn', 'comment']
    class Meta:
        model = Units
        fields ='__all__'
        exclude = ['rack', 'used_by_unit', 'owner', 'is_avaliable', 'hostname', 'mng_ip', 'in_use', 'unit_num', 'console', 'modified', 'modified_by']
