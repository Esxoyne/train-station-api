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
    CrewMemberListSerializer,
    OrderListSerializer,
    StationSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    TrainTypeSerializer,
    TrainSerializer,
    TrainListSerializer,
    TrainRetrieveSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyRetrieveSerializer,
    OrderSerializer,
)


class CrewMemberViewSet(viewsets.ModelViewSet):
    queryset = CrewMember.objects.all()
    serializer_class = CrewMemberSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return CrewMemberListSerializer

        return CrewMemberSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("origin", "destination")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteRetrieveSerializer

        return RouteSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("train_type")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer

        if self.action == "retrieve":
            return TrainRetrieveSerializer

        return TrainSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = JourneySerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related(
                "route__origin",
                "route__destination",
                "train__train_type",
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("crew")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer

        if self.action == "retrieve":
            return JourneyRetrieveSerializer

        return JourneySerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "tickets__journey__route__origin",
                "tickets__journey__route__destination",
                "tickets__journey__train__train_type",
            )

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
