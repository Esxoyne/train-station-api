from django.urls import path, include
from rest_framework import routers

from .views import (
    CrewMemberViewSet,
    StationViewSet,
    RouteViewSet,
    TrainTypeViewSet,
    TrainViewSet,
    JourneyViewSet,
    OrderViewSet,
    TicketViewSet,
)


router = routers.DefaultRouter()
router.register("crew_members", CrewMemberViewSet)
router.register("stations", StationViewSet)
router.register("routes", RouteViewSet)
router.register("train_types", TrainTypeViewSet)
router.register("trains", TrainViewSet)
router.register("journeys", JourneyViewSet)
router.register("orders", OrderViewSet)
router.register("ticket", TicketViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "train_station"
