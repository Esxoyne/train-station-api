from datetime import datetime
import os
import uuid
from django.utils import timezone
from typing import Type
from decimal import Decimal
from math import radians, sin, cos, asin, sqrt

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class CrewMember(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


def generate_file_name(info, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(info)}-{uuid.uuid4()}{extension}"

    return filename


def station_image_file_path(instance, filename):
    filename = generate_file_name(instance.name, filename)

    return os.path.join("uploads/stations/", filename)


class Station(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=7, decimal_places=4)
    longitude = models.DecimalField(max_digits=7, decimal_places=4)
    image = models.ImageField(null=True, upload_to=station_image_file_path)

    def __str__(self) -> str:
        return self.name


def haversine(
    lat1: Decimal,
    lon1: Decimal,
    lat2: Decimal,
    lon2: Decimal,
) -> int:
    """
    Haversine formula determines the distance between two points
    given their geographic coordinates
    """
    earth_radius = 6371  # radius of the Earth in km

    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return int(c * earth_radius)


class Route(models.Model):
    origin = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="outbound_routes",
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="inbound_routes",
    )

    @property
    def distance(self) -> int:
        distance = haversine(
            self.origin.latitude,
            self.origin.longitude,
            self.destination.latitude,
            self.destination.longitude,
        )
        return distance

    def __str__(self) -> str:
        return f"{self.origin} - {self.destination}"

    @staticmethod
    def validate_stations(
        origin: Station,
        destination: Station,
        error_to_raise: Type[Exception]
    ) -> None:
        if origin == destination:
            raise error_to_raise(
                {
                    "destination": "destination point "
                    "cannot be the same "
                    "as the origin point"
                }
            )

    def clean(self):
        Route.validate_stations(
            self.origin,
            self.destination,
            ValidationError,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Route, self).save(*args, **kwargs)

    class Meta:
        unique_together = ("origin", "destination")


class TrainType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


def train_image_file_path(instance, filename):
    filename = generate_file_name(instance.name, filename)

    return os.path.join("uploads/trains/", filename)


class Train(models.Model):
    name = models.CharField(max_length=255)
    cars = models.IntegerField()
    seats_in_car = models.IntegerField()
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.CASCADE,
        related_name="trains",
    )
    image = models.ImageField(null=True, upload_to=train_image_file_path)

    @property
    def capacity(self) -> int:
        return self.cars * self.seats_in_car

    def __str__(self) -> str:
        return f"{self.name} ({self.train_type})"


class Journey(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(CrewMember)

    def __str__(self) -> str:
        return (
            f"{self.route} ({self.departure_time.strftime('%d %b %Y %H:%M')})"
        )

    class Meta:
        ordering = ["departure_time"]

    @staticmethod
    def validate_time(
        departure_time: datetime,
        arrival_time: datetime,
        error_to_raise: Type[Exception],
    ) -> None:
        if arrival_time <= departure_time:
            raise error_to_raise(
                {
                    "arrival_time": "arrival time "
                    "must not be earlier than "
                    "departure time"
                }
            )
        if departure_time <= timezone.now():
            raise error_to_raise(
                {
                    "departure_time": "departure time "
                    "must not be in the past"
                }
            )

    def clean(self):
        Journey.validate_time(
            self.departure_time,
            self.arrival_time,
            ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Journey, self).save(
            force_insert, force_update, using, update_fields
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    def __str__(self) -> str:
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    car = models.IntegerField()
    seat = models.IntegerField()
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    @staticmethod
    def validate_ticket(
        car: int,
        seat: int,
        train: Train,
        error_to_raise: Type[Exception]
    ) -> None:
        for ticket_attr_value, ticket_attr_name, train_attr_name in [
            (car, "car", "cars"),
            (seat, "seat", "seats_in_car"),
        ]:
            count_attrs = getattr(train, train_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {train_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.car,
            self.seat,
            self.journey.train,
            ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self) -> str:
        return (
            f"{str(self.journey)} (car: {self.car}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("journey", "car", "seat")
        ordering = ["car", "seat"]
