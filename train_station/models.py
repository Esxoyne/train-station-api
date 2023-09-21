from decimal import Decimal
from math import radians, sin, cos, asin, sqrt

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models


class CrewMember(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Station(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=7, decimal_places=4)
    longitude = models.DecimalField(max_digits=7, decimal_places=4)

    def __str__(self) -> str:
        return self.name


def haversine(
    lat1: Decimal,
    lon1: Decimal,
    lat2: Decimal,
    lon2: Decimal,
) -> int:
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    earth_radius = 6371

    return int(c * earth_radius)


class Route(models.Model):
    source = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="outbound_routes",
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="inbound_routes",
    )
    distance = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.source.name}-{self.destination.name}"

    def save(self, *args, **kwargs):
        self.distance = haversine(
            self.source.latitude,
            self.source.longitude,
            self.destination.latitude,
            self.destination.longitude,
        )
        super().save(*args, **kwargs)


class TrainType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class Train(models.Model):
    name = models.CharField(max_length=255)
    cars = models.IntegerField()
    seats_in_car = models.IntegerField()
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.CASCADE,
        related_name="trains",
    )

    @property
    def capacity(self) -> int:
        return self.cars * self.seats_in_car

    def __str__(self) -> str:
        return self.name


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
        return f"{self.route} {self.departure_time.strftime('%d %b %Y %H:%M')}"


class Order(models.Model):
    created_at = models.DateTimeField()
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
    def validate_ticket(car, seat, train, error_to_raise):
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
