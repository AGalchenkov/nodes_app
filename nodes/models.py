from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea, CharField, ChoiceField, Field, BooleanField, \
                         HiddenInput, DateTimeField, IntegerField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.timezone import now
from bootstrap_modal_forms.forms import BSModalModelForm
from functions.ping import ping
from simple_history.models import HistoricalRecords
import ipaddress
from django.utils.ipv6 import is_valid_ipv6_address
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Customers(models.Model):
    customer = models.CharField(unique=True, max_length=50)
    def __str__(self):
        return self.customer

class Locations(models.Model):
    rack_location = models.CharField(unique=True, max_length=50)

    class Meta:
        verbose_name_plural = 'Locations'

    def __str__(self):
        return self.rack_location

class Racks(models.Model):
    location = models.ForeignKey(Locations, on_delete=models.RESTRICT)
    rack_id = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1000),
        ],
        default=999,
    )
    units_num = models.IntegerField(
        validators=[
            MinValueValidator(0, message='Отрицательное значение'),
            MaxValueValidator(48, message='Слишком большое значение(макс. 48)'),
        ]
    )
    history = HistoricalRecords()

    class Meta:
        unique_together = ['rack_id', 'location']
        ordering = ['location', 'rack_id']
        verbose_name_plural = 'Racks'

    def __str__(self):
        return f'{self.location} #{self.rack_id} ({self.units_num}U)'

class Interfaces(models.Model):
    g10 = models.IntegerField(default=0,
        validators=[
            MinValueValidator(0, message='Отрицательное значение'),
            MaxValueValidator(52, message='Максимальное значение 52'),
        ]
    )
    g40 = models.IntegerField(default=0,
        validators=[
            MinValueValidator(0, message='Отрицательное значение'),
            MaxValueValidator(52, message='Максимальное значение 52'),
        ]
    )
    g100 = models.IntegerField(default=0,
        validators=[
            MinValueValidator(0, message='Отрицательное значение'),
            MaxValueValidator(52, message='Максимальное значение 52'),
        ]
    )

    class Meta:
        verbose_name_plural = 'Interfaces'


class RdpModels(models.Model):
    rdp_model = models.CharField(unique=True, max_length=20)

    class Meta:
        verbose_name_plural = 'RdpModels'

    def __str__(self):
        return self.rdp_model

class Models(models.Model):
    model_name = models.CharField(unique=True, max_length=20)
    #interface = models.ForeignKey(Interfaces, null=True, blank=True, on_delete=models.CASCADE)
    units_takes = models.IntegerField(default=1,
        validators=[
            MinValueValidator(1, message='Отрицательное значение'),
            MaxValueValidator(5, message='Слишком большое значение(макс. 5)'),
        ]
    )
    active = models.BooleanField(default=True)
    is_rdp = models.BooleanField(default=False)
    rdp_name = models.ForeignKey(RdpModels, null=True, blank=True, on_delete=models.RESTRICT)

    class Meta:
        verbose_name_plural = 'Models'

    def __str__(self):
        return self.model_name

class Vendors(models.Model):
    vendor_name = models.CharField(unique=True, max_length=20)

    class Meta:
        verbose_name_plural = 'Vendors'

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
        verbose_name_plural = 'VendorModels'

class Consoles(models.Model):
    console = models.CharField(unique=True, max_length=5)

    class Meta:
        verbose_name_plural = 'Consoles'

    def __str__(self):
        return self.console


class Comments(models.Model):
    #unit = models.OneToOneField(Units, null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    text = models.CharField(max_length=1000, blank=True, null=True)
    #pub_date = models.DateTimeField(default=now().replace(microsecond=0))
    pub_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Comments'

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
            MinValueValidator(1, message='Отрицательное значение'),
            MaxValueValidator(4096, message='Слишком большое значение(макс. 4096)'),
        ]
    )
    ipmi = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Appliances'

    def __str__(self):
        return self.appliance

#Little Secret

class Ram(models.Model):
    ram = models.IntegerField(
        validators=[
            MinValueValidator(16, message='Отрицательное значение'),
            MaxValueValidator(4096, message='Слишком большое значение(макс. 4096)'),
        ]
    )

    class Meta:
        verbose_name_plural = 'Ram'

    def __str__(self):
        return str(self.ram) + 'G'

class TelegramToken(models.Model):
    telegram_bot_name = models.CharField(null=True, blank=True, max_length=100)
    token = models.CharField(null=True, blank=True, max_length=150)

class TelegramUser(models.Model):
    telegram_id = models.IntegerField(null=True, blank=True)
    telegram_name = models.CharField(unique=True, max_length=50)
    real_name = models.CharField(null=True, blank=True, max_length=50)

class LittleSecret(models.Model):
    in_use = models.BooleanField(default=False)
    owner = models.ForeignKey(TelegramUser, null=True, blank=True, default=None, related_name='ls_owner', on_delete=models.SET_DEFAULT)

    def __str__(self):
        return f'LittleSecret Node #{self.id}'

class Units(models.Model):
    in_use = models.BooleanField(default=False)
    used_by_unit = models.CharField(blank=True, default='', max_length=3)
    owner = models.ForeignKey(User, null=True, blank=True, default=None, related_name='owner', on_delete=models.SET_DEFAULT)
    expired_date = models.DateTimeField(null=True, blank=True)
    is_notifi_send = models.BooleanField(default=False)
    rack = models.ForeignKey(Racks, null=True, blank=True, default=None,  on_delete=models.CASCADE)
    unit_num = models.IntegerField(blank=False,
        validators=[
            MinValueValidator(0, message='Отрицательное значение'),
            MaxValueValidator(48, message='Слишком большое значение(макс. 48)')
        ]
    )
    model = models.ForeignKey(Models, null=True, blank=True, on_delete=models.RESTRICT)
    ram = models.ForeignKey(Ram, null=True, blank=True, on_delete=models.RESTRICT)
    vendor = models.ForeignKey(Vendors, null=True, blank=True, on_delete=models.RESTRICT)
    power = models.ForeignKey(PowerSupply, null=True, blank=True, on_delete=models.RESTRICT)
    vendor_model = models.ForeignKey(VendorModels,null=True, blank=True, on_delete=models.RESTRICT)
    console = models.ForeignKey(Consoles, null=True, blank=True, on_delete=models.RESTRICT)
    mng_ip = models.GenericIPAddressField(blank=True, null=True)
    ipmi_bmc = models.GenericIPAddressField(blank=True, null=True)
    has_ipmi = models.BooleanField(default=False)
    ipmi_is_avaliable = models.BooleanField(default=False)
    appliance = models.ForeignKey(Appliances, null=True, blank=True, default=None,  on_delete=models.RESTRICT)
    rdp_firmware = models.CharField(blank=True, max_length=30)
    g10 = models.IntegerField(default=0,
        validators=[
            MinValueValidator(0, message='Отрицательное значение'),
            MaxValueValidator(52, message='Максимальное значение 52'),
        ]
    )
    g40 = models.IntegerField(default=0,
        validators=[
            MinValueValidator(0, message='Отрицательное значение'),
            MaxValueValidator(52, message='Максимальное значение 52'),
        ]
    )
    g100 = models.IntegerField(default=0,
        validators=[
            MinValueValidator(0, message='Отрицательное значение'),
            MaxValueValidator(52, message='Максимальное значение 52'),
        ]
    )
    is_avaliable = models.BooleanField(default=False)
    sn = models.CharField(blank=True, max_length=30)
    hostname = models.CharField(blank=True, max_length=15)
    release_date = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(editable=False, default=now().replace(microsecond=0))
    modified = models.DateTimeField(default=now().replace(microsecond=0))
    modified_by = models.ForeignKey(User, null=True, blank=True, default=None, related_name='modified_by', on_delete=models.SET_DEFAULT)
    comment = models.OneToOneField(Comments, null=True, blank=True, default=None, on_delete=models.SET_DEFAULT)
    history = HistoricalRecords()

    class Meta:
        unique_together = ['rack_id', 'unit_num']
        permissions = (
            ('can_edit_unit', 'edit unit'),
            ('can_view_unit', 'view unit'),
            ('can_set_owner', 'owner unit'),
        )
        verbose_name_plural = 'Units'

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


class UnitRebaseForm(ModelForm):
    model = Units
    class Meta:
        model = Units
        fields = ['rack', 'unit_num']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rack'].widget.attrs['id'] = 'rebase_rack'
        self.fields['unit_num'].widget.attrs['id'] = 'rebase_unit_num'

    def clean(self):
        cleaned_data = super().clean()
        rack = cleaned_data.get('rack')
        unit_num = cleaned_data.get('unit_num')
        model = Units.objects.get(rack=rack, unit_num=unit_num).model
        if Units.objects.get(rack=rack, unit_num=unit_num).model:
            raise ValidationError('Юнит назначения занят')
        return self.cleaned_data


class UnitForm(ModelForm):
    error_css_class = 'error'
    rack = Field(disabled=True)
    in_use = Field(disabled=True)
    expired_date = DateTimeField(input_formats=['%d-%m-%Y %H:%M'], required=False)
    modified = Field(disabled=True)
    unit_num = CharField(disabled=True)
    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3, 'style': 'resize:none;'}), required=False)
    comment_author = CharField(disabled=True, required=False)
    comment_pub_date = CharField(disabled=True, required=False)
    modified_by = CharField(disabled=True, required=False)
    mng_ip = Field(required=False, error_messages={'invalid': 'Введите верный ipv4/ipv6 адрес.'})
    ipmi_bmc = Field(required=False, error_messages={'invalid': 'Введите верный ipv4/ipv6 адрес.'})
    #g10 = Field(required=False)
    #g40 = Field(required=False)
    #g100 = Field(required=False)
    #ram = CharField(required=False, disabled=True)
    field_order = [
        'in_use', 'owner', 'rack', 'unit_num', 'model', 'vendor', 'power', 'vendor_model',
        'console', 'has_ipmi', 'ipmi_bmc', 'appliance', 'mng_ip', 'ram', 'g10', 'sn', 'g40', 'hostname', 'g100', 'modified',  'modified_by',
        'comment_author', 'comment_pub_date',
    ]
    model = Units
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user = kwargs.pop('user', None)
        self.role = kwargs.pop('role', None)
        super().__init__(*args, **kwargs)
        self.initial['rack'] = kwargs['instance'].rack
        #try:
        #    self.initial['ram'] = kwargs['instance'].appliance.ram
        #except AttributeError:
        #    self.initial['ram'] = None
        try:
            self.initial['comment_author'] = kwargs['instance'].comment.author
            self.initial['comment_pub_date'] = kwargs['instance'].comment.pub_date
        except AttributeError:
            self.initial['comment_author'] = None
        try:
            #self.initial['expired_date'] = kwargs['instance'].expired_date.strftime('%d/%m/%Y %H:%M')
            self.initial['expired_date'] = kwargs['instance'].expired_date
        except AttributeError:
            self.initial['expired_date'] = None

    def add_fatboy(self, unit_num, model, rack):
        other_unit_used_list = []
        start_unit = int(unit_num) + 1
        end_unit = int(unit_num) + int(model.units_takes)
        if end_unit > rack.units_num:
            raise ValidationError('Данная моедль занимает слишком много юнитов.')
        list = [i for i in range(start_unit, end_unit)]
        for item in list:

            try:
                u = Units.objects.get(rack=rack, unit_num=item)
                if u.model or u.in_use == True:
                    raise ValidationError(f'Данная модель занимает {model.units_takes}U, но следующий юнит занят (U{u.unit_num})')
                else:
                    use_u = Units.objects.get(rack=rack, unit_num=item)
                    use_u.used_by_unit = unit_num
                    other_unit_used_list.append(use_u)
                    continue
            except ObjectDoesNotExist:
                raise ValidationError('Внутренняя ошибка. Обратитесь к администратору.')
        Units.objects.bulk_update(other_unit_used_list, ['used_by_unit'])

    def remove_fatboy(self, unit_num, old_model, rack):
        start_unit = int(unit_num) + 1
        end_unit = int(unit_num) + int(old_model.units_takes)
        list = [i for i in range(start_unit, end_unit)]
        for item in list:
            use_u = Units.objects.get(rack=rack, unit_num=item)
            use_u.used_by_unit = ''
            use_u.save()
            continue

    def change_fatboy(self, unit_num, model, old_model, rack):
        start_unit = int(unit_num) + 1
        end_unit = int(unit_num) + int(old_model.units_takes)
        if model.units_takes > old_model.units_takes:
            diff = model.units_takes - old_model.units_takes
        else:
            diff = old_model.units_takes - model.units_takes
            list = [i for i in range(end_unit - diff, end_unit)]
            for item in list:
                use_u = Units.objects.get(rack=rack, unit_num=item)
                use_u.used_by_unit = ''
                use_u.save()
                continue

    def clean(self):
        passive_model = Models.objects.values_list('model_name', flat=True).filter(active=False)
        other_unit_used_list = []
        user = self.user
        cleaned_data = super().clean()
        modified_by = cleaned_data.get('modified_by')
        comment = cleaned_data.get('comment')
        if not comment:
            cleaned_data['comment'] = None
            cleaned_data['comment_pub_date'] = None
        if comment in self.changed_data:
            cleaned_data['comment'] = Units.objects.get(id=comment).comment
        mng_ip = cleaned_data.get('mng_ip')
        if mng_ip and 'mng_ip' in self.changed_data:
            try:
                if ping(mng_ip):
                    self.instance.is_avaliable = True
                else:
                    self.instance.is_avaliable = False
            except (OSError, TypeError):
                self.instance.is_avaliable = False
        ipmi_bmc = cleaned_data.get('ipmi_bmc')
        if 'ipmi_bmc' in self.changed_data:
            try:
                if ping(ipmi_bmc):
                    self.instance.ipmi_is_avaliable = True
                else:
                    self.instance.ipmi_is_avaliable = False
            except (OSError, TypeError):
                self.instance.ipmi_is_avaliable = False
        owner = cleaned_data.get('owner')
        unit_num = cleaned_data.get('unit_num')
        rack = cleaned_data.get('rack')
        if self.has_changed():
            cleaned_data['modified_by'] = user
            cleaned_data['modified'] = now().replace(microsecond=0)
            if self.role >= 3:
                raise ValidationError('Недостаточно прав!')
            old_owner = Units.objects.get(rack=rack, unit_num=unit_num).owner
            if 'owner' in self.changed_data and self.role > 1 and old_owner and old_owner != user:
                #old_owner = Units.objects.get(rack=rack, unit_num=unit_num).owner
                raise ValidationError('Вам не доступно изменение чужого бронирования.')
            elif (('owner' in self.changed_data and owner and self.role > 1 and old_owner and old_owner == user) or
                 ('owner' in self.changed_data and owner != user and self.role > 1 and not old_owner)):
                raise ValidationError('Вам доступно бронирование только для себя.')
            if self.role > 1 and owner and owner != user:
                raise ValidationError('Вам не доступно изменение чужого бронирования.')
        else:
            if not modified_by:
                cleaned_data['modified_by'] = None
            else:
                pass
                cleaned_data['modified_by'] = User.objects.get(id=modified_by)
        in_use = cleaned_data.get('in_use')
        has_ipmi = cleaned_data.get('has_ipmi')
        sn = cleaned_data.get('sn')
        model = cleaned_data.get('model')
        vendor = cleaned_data.get('vendor')
        power = cleaned_data.get('power')
        expired_date = cleaned_data.get('expired_date')
        old_model = Units.objects.get(rack=rack, unit_num=unit_num).model
        old_model_units_takes = old_model.units_takes if hasattr(old_model, 'units_takes') else 0
        if model:
            if model.model_name in list(passive_model):
                self.cleaned_data['g10'] = 0
                self.cleaned_data['g40'] = 0
                self.cleaned_data['g100'] = 0
                print('@#$%^&*(@#$%^&*(#$%^&*(#$%^&*(#$%^&*#$%^&*')
                #self.cleaned_data['appliance'] = None
                #self.changed_data.append('model')
                if old_model_units_takes > 1:
                    self.remove_fatboy(unit_num, old_model, rack)
                return self.cleaned_data
            if sn == '':
                raise ValidationError('Модель и серийный номер заполняются вместе')
            if vendor == None:
                raise ValidationError('Модель и вендор заполняются вместе')
        if owner:
            if not expired_date:
                self.cleaned_data['expired_date'] = datetime.now() + timedelta(hours=8)
            self.cleaned_data['in_use'] = True
        else:
            if expired_date:
                if user != old_owner and self.role > 1:
                    raise ValidationError('Указана только дата бронирования, укажите владельца.')
            self.cleaned_data['in_use'] = False
            self.cleaned_data['expired_date'] = None

        if expired_date:
            delta = expired_date - datetime.now()
            if delta.total_seconds() < 0:
                raise ValidationError('Дата истечения брони меньше текущей.')
            if delta.total_seconds() < 900:
                cleaned_data['small_delta'] = True
            else:
                cleaned_data['small_delta'] = False
        if mng_ip and not model:
            raise ValidationError('Укажите модель')
        if ipmi_bmc and not has_ipmi:
            raise ValidationError("Укажите 'has_ipmi' если указан 'ipmi_bmc' ip")
        if sn:
            if model == None:
                raise ValidationError('Модель и серийный номер заполняются вместе')
            sn_unit = Units.objects.filter(sn=sn).exclude(unit_num=unit_num, rack=rack)
            if sn_unit:
                raise ValidationError(
                    f'''
                    Юнит с таким серийным номером уже существует <a class="clr_blue underline"
                    href="/rack/{sn_unit[0].rack.id}/unit_detail/{sn_unit[0].unit_num}">
                    {sn_unit[0].rack.location} #{sn_unit[0].rack.rack_id} U{sn_unit[0].unit_num}</a>
                    '''
                )
            #raise ValidationError('not in use unit must have no owner')
        if model:
            if old_model == model:
                pass
            else:
                if model.units_takes > 1 and old_model_units_takes > 1 and model.units_takes < old_model_units_takes:
                    self.change_fatboy(unit_num, model, old_model, rack)
                elif model.units_takes > 1 and old_model == None or \
                        model.units_takes > 1 and old_model_units_takes > 1 and model.units_takes > old_model_units_takes or \
                        model.units_takes > 1 and old_model_units_takes == 1:
                    self.add_fatboy(unit_num, model, rack)
                elif model.units_takes == 1 and old_model_units_takes > 1:
                    self.remove_fatboy(unit_num, old_model, rack)
        elif model == None and old_model_units_takes > 1:
            self.remove_fatboy(unit_num, old_model, rack)

        return self.cleaned_data

    class Meta:
        model = Units
        fields = '__all__'
        exclude = ['used_by_unit', 'comment', 'is_avaliable', 'ipmi_is_avaliable', 'is_notifi_send']
        labels = {
            'g10': '10G',
            'g40': '40G',
            'g100': '100G',
        }


class UnitFormDisabled(ModelForm):
    error_css_class = 'error'
    rack = Field(disabled=True)
    modified = Field(disabled=True)
    unit_num = CharField(disabled=True)
    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3}), required=False, disabled=True)
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

    class Meta:
        model = Units
        fields = '__all__'
        exclude = ['used_by_unit', 'comment', 'is_avaliable']


class CommentForm(ModelForm):
    class Meta:
        model = Comments
        fields = '__all__'


class SearchForm(ModelForm):

    comment = CharField(widget=Textarea(attrs={'cols': 40, 'rows': 3, 'style': 'resize:none;'}), required=False)
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
    ipmi_is_avaliable_choises = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )
    has_ipmi = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )
    has_10G = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )
    has_40G = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )
    has_100G = (
        (1, 'no matter'),
        (2, 'yes'),
        (3, 'no'),
    )
    has_model = ChoiceField(choices=has_model_choises)
    has_ipmi = ChoiceField(choices=has_ipmi)
    has_10G = ChoiceField(choices=has_10G)
    has_40G = ChoiceField(choices=has_40G)
    has_100G = ChoiceField(choices=has_100G)
    is_avaliable = ChoiceField(choices=is_avaliable_choises)
    ipmi_is_avaliable = ChoiceField(choices=ipmi_is_avaliable_choises)

    field_order = [
        'owner', 'rack', 'model', 'vendor', 'power', 'vendor_model',
        'mng_ip', 'ipmi_bmc', 'appliance', 'sn', 'ram', 'hostname', 'comment',
        'has_ipmi', 'ipmi_is_avaliable', 'is_avaliable', 'has_10G', 'has_40G', 'has_100G',
        'has_model',
    ]

    model = Units

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Units
        exclude = ['used_by_unit', 'in_use', 'unit_num', 'console',
                   'modified', 'modified_by', 'expired_date', 'g10',
                   'g40', 'g100', 'ipmi', 'ipmi_is_avaliable', 'rdp_firmware', 'is_notifi_send'
        ]

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

class RackCreateForm(ModelForm):

    class Meta:
        model = Racks
        fields = '__all__'

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
