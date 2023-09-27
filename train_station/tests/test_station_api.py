import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import (
    Station,
)

STATION_URL = reverse("train_station:station-list")


def sample_station(**params):
    defaults = {
        "name": "Kyiv",
        "latitude": 50.4404,
        "longitude": 30.4867,
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


def image_upload_url(station_id):
    """Return URL for station image upload"""
    return reverse("train_station:station-upload-image", args=[station_id])


def detail_url(station_id):
    return reverse("train_station:station-detail", args=[station_id])


class StationImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@example.com", "admin12345"
        )
        self.client.force_authenticate(self.user)
        self.station = sample_station()

    def tearDown(self):
        self.station.refresh_from_db()
        self.station.image.delete()

    def test_upload_image_to_station(self):
        """Test uploading an image to station"""
        url = image_upload_url(self.station.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.station.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.station.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.station.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_station_list(self):
        url = STATION_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Lviv",
                    "latitude": 49.8403,
                    "longitude": 23.9930,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        station = Station.objects.get(name="Lviv")
        self.assertFalse(station.image)

    def test_image_url_is_shown_on_station_detail(self):
        url = image_upload_url(self.station.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.station.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_station_list(self):
        url = image_upload_url(self.station.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(STATION_URL)

        self.assertIn("image", res.data[0].keys())
