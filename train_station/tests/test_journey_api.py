import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import (
    Route,
    Journey,
    Station,
    Train,
    CrewMember,
    TrainType,
)
from train_station.serializers import (
    JourneyListSerializer,
    JourneyRetrieveSerializer,
)


JOURNEY_URL = reverse("train_station:journey-list")


def sample_station(**params):
    defaults = {
        "name": "Kyiv",
        "latitude": 50.4404,
        "longitude": 30.4867,
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


def sample_route(origin, destination, **params):
    defaults = {
        "origin": origin,
        "destination": destination,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


def sample_train_type(**params):
    defaults = {
        "name": "Intercity",
    }
    defaults.update(params)

    return TrainType.objects.create(**defaults)


def sample_train(train_type, **params):
    defaults = {
        "name": "ICE 4",
        "cars": 5,
        "seats_in_car": 15,
        "train_type": train_type,
    }
    defaults.update(params)

    return Train.objects.create(**defaults)


def sample_crew(**params):
    defaults = {"first_name": "Alice", "last_name": "Smith"}
    defaults.update(params)

    return CrewMember.objects.create(**defaults)


def sample_journey(route, train, **params):
    defaults = {
        "route": route,
        "train": train,
        "departure_time": datetime.datetime(2024, 10, 10),
        "arrival_time": datetime.datetime(2024, 10, 20),
    }
    defaults.update(params)

    return Journey.objects.create(**defaults)


def detail_url(journey_id):
    return reverse("train_station:journey-detail", args=[journey_id])


class UnauthenticatedJourneyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(JOURNEY_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedJourneyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com",
            "user12345",
        )
        self.client.force_authenticate(self.user)

        train_type = sample_train_type()

        self.train_1 = sample_train(name="ICE 3", train_type=train_type)
        self.train_2 = sample_train(name="ICE TD", train_type=train_type)

        self.crew_1 = sample_crew()
        self.crew_2 = sample_crew(first_name="Bob")

        self.station_1 = sample_station()
        self.station_2 = sample_station(name="Lviv")

        self.route_1 = sample_route(self.station_1, self.station_2)
        self.route_2 = sample_route(self.station_2, self.station_1)

        self.journey_1 = sample_journey(
            train=self.train_1,
            route=self.route_1,
        )
        self.journey_2 = sample_journey(
            train=self.train_2,
            route=self.route_2,
            departure_time=datetime.datetime(2024, 10, 12),
            arrival_time=datetime.datetime(2024, 10, 17),
        )

        self.journey_1.crew.add(self.crew_1)
        self.journey_2.crew.add(self.crew_1, self.crew_2)

        self.serializer_1 = JourneyListSerializer(self.journey_1)
        self.serializer_2 = JourneyListSerializer(self.journey_2)

    def test_list_journeys(self):
        res = self.client.get(JOURNEY_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 2)

    def test_filter_journeys_by_route(self):
        res = self.client.get(JOURNEY_URL, {"route": self.route_1.id})

        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_journeys_by_departure(self):
        res = self.client.get(JOURNEY_URL, {"departure": "2024-10-10"})

        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_journeys_by_arrival(self):
        res = self.client.get(JOURNEY_URL, {"arrival": "2024-10-20"})

        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_journeys_by_train(self):
        res = self.client.get(JOURNEY_URL, {"train": self.train_1.id})

        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_journeys_by_crew(self):
        res = self.client.get(
            JOURNEY_URL,
            {"crew": f"{self.crew_1.id},{self.crew_2.id}"}
        )

        self.assertEqual(len(res.data["results"]), 1)

    def test_retrieve_journey_detail(self):
        url = detail_url(self.journey_1.id)
        res = self.client.get(url)

        serializer = JourneyRetrieveSerializer(self.journey_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_journey_forbidden(self):
        payload = {
            "route": self.route_1,
            "train": self.train_1,
            "departure_time": datetime.datetime(2024, 10, 12),
            "arrival_time": datetime.datetime(2024, 10, 15),
        }

        res = self.client.post(JOURNEY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_journey_forbidden(self):
        url = detail_url(self.journey_1.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminJourneyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com",
            "user12345",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_journey(self):
        station_1 = sample_station()
        station_2 = sample_station(name="Lviv")
        train_type = sample_train_type()
        route = sample_route(station_1, station_2)
        train = sample_train(train_type)

        crew = sample_crew()

        payload = {
            "route": route.id,
            "train": train.id,
            "departure_time": datetime.datetime(2024, 10, 12),
            "arrival_time": datetime.datetime(2024, 10, 15),
            "crew": crew.id,
        }

        res = self.client.post(JOURNEY_URL, payload)
        journey = Journey.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(route, journey.route)
        self.assertEqual(train, journey.train)
        self.assertIn(crew, journey.crew.all())
