from django.shortcuts import render

from rest_framework import mixins, viewsets

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
from .serializers import (
    CrewMemberSerializer,
    StationSerializer,
    RouteSerializer,
    TrainTypeSerializer,
    TrainSerializer,
    JourneySerializer,
    OrderSerializer,
    TicketSerializer,
)


class CrewMemberViewSet(viewsets.ModelViewSet):
    queryset = CrewMember.objects.all()
    serializer_class = CrewMemberSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = JourneySerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
