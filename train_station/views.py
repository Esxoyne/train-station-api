from datetime import datetime

from django.db.models import F, Count
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .permissions import IsAdminOrAuthenticatedReadOnly
from .models import (
    CrewMember,
    Station,
    Route,
    TrainType,
    Train,
    Journey,
    Order,
)
from .serializers import (
    CrewMemberSerializer,
    CrewMemberListSerializer,
    OrderListSerializer,
    StationImageSerializer,
    StationSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    TrainImageSerializer,
    TrainTypeSerializer,
    TrainSerializer,
    TrainListSerializer,
    TrainRetrieveSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyRetrieveSerializer,
    OrderSerializer,
)


class StandardResultSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CrewMemberViewSet(viewsets.ModelViewSet):
    queryset = CrewMember.objects.all()
    serializer_class = CrewMemberSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return CrewMemberListSerializer

        return CrewMemberSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "upload_image":
            return StationImageSerializer

        return StationSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading an image to a specific station"""
        station = self.get_object()
        serializer = self.get_serializer(station, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset

        origin = self.request.query_params.get("origin")
        destination = self.request.query_params.get("destination")

        if origin:
            queryset = queryset.filter(origin__id=int(origin))

        if destination:
            queryset = queryset.filter(destination__id=int(destination))

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
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    pagination_class = StandardResultSetPagination
    serializer_class = TrainSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset

        type = self.request.query_params.get("type")

        if type:
            queryset = queryset.filter(train_type__id=int(type))

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("train_type")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer

        if self.action == "retrieve":
            return TrainRetrieveSerializer

        if self.action == "upload_image":
            return TrainImageSerializer

        return TrainSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading an image to a specific train"""
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    pagination_class = StandardResultSetPagination
    serializer_class = JourneySerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        route = self.request.query_params.get("route")
        departure = self.request.query_params.get("departure")
        arrival = self.request.query_params.get("arrival")
        train = self.request.query_params.get("train")
        crew = self.request.query_params.get("crew")

        if route:
            queryset = queryset.filter(route__id=int(route))

        if departure:
            try:
                departure = datetime.strptime(departure, "%Y-%m-%d").date()
                queryset = queryset.filter(departure_time__date=departure)
            except ValueError:
                return None

        if arrival:
            try:
                arrival = datetime.strptime(arrival, "%Y-%m-%d").date()
                queryset = queryset.filter(arrival_time__date=arrival)
            except ValueError:
                return None

        if train:
            queryset = queryset.filter(train__id=int(train))

        if crew:
            crew_ids = self._params_to_ints(crew)
            for crew_id in crew_ids:
                queryset = queryset.filter(crew__id=crew_id)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related(
                "route__origin",
                "route__destination",
                "train__train_type",
            ).prefetch_related("crew")

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("train__cars") * F("train__seats_in_car")
                    - Count("tickets")
                )
            ).order_by("departure_time")

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer

        if self.action == "retrieve":
            return JourneyRetrieveSerializer

        return JourneySerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    pagination_class = StandardResultSetPagination
    serializer_class = OrderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "tickets__journey__route__origin",
                "tickets__journey__route__destination",
                "tickets__journey__train__train_type",
                "tickets__journey__crew",
            )

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
