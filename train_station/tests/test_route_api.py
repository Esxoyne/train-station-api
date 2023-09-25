from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import (
    Route,
    Station,
)
from train_station.serializers import (
    RouteListSerializer,
    RouteRetrieveSerializer,
)

ROUTE_URL = reverse("train_station:route-list")

def sample_station(**params):
    defaults = {
        "name": "Kyiv",
        "latitude": 50.4404,
        "longitude": 30.4867,
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


def sample_route(**params):
    defaults = {
        "origin": Station.objects.get(pk=1),
        "destination": Station.objects.get(pk=2),
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


def detail_url(route_id):
    return reverse("train_station:route-detail", args=[route_id])


class UnauthenticatedRouteAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com",
            "user12345",
        )
        self.client.force_authenticate(self.user)

        self.station_1 = sample_station()
        self.station_2 = sample_station(name="Lviv")

        self.route_1 = sample_route()
        self.route_2 = sample_route(
            origin=self.station_2,
            destination=self.station_1
        )

        self.serializer_1 = RouteListSerializer(self.route_1)
        self.serializer_2 = RouteListSerializer(self.route_2)

    def test_list_routes(self):
        res = self.client.get(ROUTE_URL)

        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_routes_by_origin(self):
        res = self.client.get(ROUTE_URL, {"origin": self.station_1.id})

        self.assertIn(self.serializer_1.data, res.data)
        self.assertNotIn(self.serializer_2.data, res.data)

    def test_filter_routes_by_destination(self):
        res = self.client.get(ROUTE_URL, {"destination": self.station_2.id})

        self.assertIn(self.serializer_1.data, res.data)
        self.assertNotIn(self.serializer_2.data, res.data)

    def test_retrieve_route_detail(self):
        url = detail_url(self.route_1.id)
        res = self.client.get(url)

        serializer = RouteRetrieveSerializer(self.route_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        station = sample_station(name="Kharkiv")
        payload = {
            "origin": self.station_1.id,
            "destination": station.id,
        }

        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_route_forbidden(self):
        url = detail_url(self.route_1.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com",
            "user12345",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        origin = sample_station()
        destination = sample_station(name="Kharkiv")
        payload = {
            "origin": origin.id,
            "destination": destination.id,
        }

        res = self.client.post(ROUTE_URL, payload)

        route = Route.objects.get(pk=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(origin, route.origin)
        self.assertEqual(destination, route.destination)
