from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Models, Customers, Locations, Racks, Units, Comments, PowerSupply, Vendors, VendorModels, Consoles, Appliances, LittleSecret, TelegramUser

admin.site.register(Models)
admin.site.register(Customers)
admin.site.register(Locations)
admin.site.register(Racks, SimpleHistoryAdmin)
admin.site.register(Units, SimpleHistoryAdmin)
admin.site.register(Comments)
admin.site.register(PowerSupply)
admin.site.register(Vendors)
admin.site.register(VendorModels)
admin.site.register(Consoles)
admin.site.register(Appliances)
admin.site.register(LittleSecret)
admin.site.register(TelegramUser)
