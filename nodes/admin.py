from django.contrib import admin

from .models import Models, Customers, Locations, Racks, Units, Comments, PowerSupply, Vendors, VendorModels, Consoles

admin.site.register(Models)
admin.site.register(Customers)
admin.site.register(Locations)
admin.site.register(Racks)
admin.site.register(Units)
admin.site.register(Comments)
admin.site.register(PowerSupply)
admin.site.register(Vendors)
admin.site.register(VendorModels)
admin.site.register(Consoles)
