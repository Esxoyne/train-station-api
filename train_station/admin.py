from django.contrib import admin

from .models import (
    CrewMember,
    Station,
    Route,
    TrainType,
    Train,
    Journey,
    Order,
    Ticket,
)


admin.site.register(CrewMember)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(TrainType)
admin.site.register(Train)
admin.site.register(Journey)
admin.site.register(Order)
admin.site.register(Ticket)
