import datetime
import tempfile
import os

from PIL import Image
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
    TrainListSerializer,
    TrainRetrieveSerializer,
)
from train_station.tests.test_journey_api import JOURNEY_URL

TRAIN_URL = reverse("train_station:train-list")


def sample_route(**params):
    origin = Station.objects.create(
        name="Kyiv",
        latitude=50.4404,
        longitude=30.4867,
    )
    destination = Station.objects.create(
        name="Lviv",
        latitude=49.8403,
        longitude=23.9930,
    )
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


def sample_train(**params):
    train_type = TrainType.objects.get(pk=1)

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


def sample_journey(**params):
    route = sample_route()
    train = Train.objects.get(pk=1)

    defaults = {
        "route": route,
        "train": train,
        "departure_time": datetime.datetime(2024, 10, 10),
        "arrival_time": datetime.datetime(2024, 10, 20),
    }
    defaults.update(params)

    return Journey.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for train image upload"""
    return reverse("train_station:train-upload-image", args=[train_id])


def detail_url(train_id):
    return reverse("train_station:train-detail", args=[train_id])


class TrainImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@example.com", "admin12345"
        )
        self.client.force_authenticate(self.user)
        self.train_type = sample_train_type()
        self.train = sample_train(train_type=self.train_type)
        self.journey = sample_journey(train=self.train)

    def tearDown(self):
        self.train.refresh_from_db()
        self.train.image.delete()

    def test_upload_image_to_train(self):
        """Test uploading an image to train"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.train.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_train_list(self):
        url = TRAIN_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Train",
                    "cars": 5,
                    "seats_in_car": 15,
                    "train_type": [1],
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(name="Train")
        self.assertFalse(train.image)

    def test_image_url_is_shown_on_train_detail(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.train.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_train_list(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(TRAIN_URL)

        self.assertIn("image", res.data["results"][0].keys())

    def test_image_url_is_shown_on_journey_list(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(JOURNEY_URL)

        self.assertIn("train_image", res.data["results"][0].keys())


class UnauthenticatedTrainAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com",
            "user12345",
        )
        self.client.force_authenticate(self.user)

        self.type_1 = sample_train_type(name="Intercity")
        self.type_2 = sample_train_type(name="High-speed Rail")

        self.train_1 = sample_train(name="ICE 3", train_type=self.type_1)
        self.train_2 = sample_train(name="ICE TD", train_type=self.type_1)
        self.train_3 = sample_train(name="ICE 4", train_type=self.type_2)

        self.serializer_1 = TrainListSerializer(self.train_1)
        self.serializer_2 = TrainListSerializer(self.train_2)
        self.serializer_3 = TrainListSerializer(self.train_3)

    def test_list_trains(self):
        res = self.client.get(TRAIN_URL)

        trains = Train.objects.all()
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_trains_by_type(self):
        res = self.client.get(TRAIN_URL, {"type": 1})

        self.assertIn(self.serializer_1.data, res.data["results"])
        self.assertIn(self.serializer_2.data, res.data["results"])
        self.assertNotIn(self.serializer_3.data, res.data["results"])

    def test_retrieve_train_detail(self):
        url = detail_url(self.train_1.id)
        res = self.client.get(url)

        serializer = TrainRetrieveSerializer(self.train_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        payload = {
            "name": "S-102",
            "cars": 5,
            "seats_in_car": 15,
            "train_type": self.type_2,
        }

        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_train_forbidden(self):
        url = detail_url(self.train_1.id)

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

    def test_create_train(self):
        train_type = sample_train_type()
        payload = {
            "name": "S-102",
            "cars": 5,
            "seats_in_car": 15,
            "train_type": train_type.id,
        }

        res = self.client.post(TRAIN_URL, payload)

        train = Train.objects.get(pk=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in ("name", "cars", "seats_in_car"):
            self.assertEqual(payload[key], getattr(train, key))
        self.assertEqual(train_type, train.train_type)
