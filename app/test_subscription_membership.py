from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Usuario, Suscripcion, WebpayTransaction

from .subscription_membership import (
    active_subscription_ids,
    has_active_subscription,
    subscription_periods,
)


class SubscriptionMembershipTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.artist = User.objects.create_user(
            username="membership_artist"
        )

        producer = User.objects.create_user(
            username="membership_producer"
        )

        self.artist_profile = Usuario.objects.create(
            user=self.artist,
            tipo_usu=Usuario.ARTISTA,
        )

        producer_profile = Usuario.objects.create(
            user=producer,
            tipo_usu=Usuario.PRODUCTOR,
        )

        self.plan = Suscripcion.objects.create(
            detalle="Plan mensual",
            precio=15000,
            user=producer_profile,
        )

        self.now = timezone.now()
        self.sequence = 0

    def payment(
        self,
        fulfilled_at=None,
        status=WebpayTransaction.ESTADO_AUTORIZADO,
        archived=False,
    ):
        self.sequence += 1

        return WebpayTransaction.objects.create(
            user=self.artist,
            suscripcion=self.plan,
            buy_order=f"membership-test-{self.sequence}",
            session_id=self.artist.username,
            amount=self.plan.precio,
            status=status,
            fulfilled_at=fulfilled_at,
            archived_for_review=archived,
            archived_at=self.now if archived else None,
            archive_reason="Test" if archived else "",
        )

    def test_confirmed_payment_activates_membership(self):
        self.payment(fulfilled_at=self.now)

        self.assertTrue(
            has_active_subscription(
                self.artist.pk, self.plan.pk, self.now
            )
        )

    def test_membership_expires_after_thirty_days(self):
        self.payment(
            fulfilled_at=self.now - timedelta(days=30)
        )

        self.assertFalse(
            has_active_subscription(
                self.artist.pk, self.plan.pk, self.now
            )
        )

    def test_rejected_payment_does_not_activate_membership(self):
        self.payment(
            status=WebpayTransaction.ESTADO_CANCELADO
        )

        self.assertEqual(
            active_subscription_ids(self.artist.pk, self.now),
            [],
        )

    def test_pending_payment_does_not_activate_membership(self):
        self.payment(
            status=WebpayTransaction.ESTADO_PENDIENTE
        )

        self.assertEqual(
            active_subscription_ids(self.artist.pk, self.now),
            [],
        )

    def test_authorized_without_fulfillment_is_not_active(self):
        self.payment()

        self.assertFalse(
            has_active_subscription(
                self.artist.pk, self.plan.pk, self.now
            )
        )

    def test_archived_payment_is_not_active(self):
        self.payment(fulfilled_at=self.now, archived=True)

        self.assertEqual(
            active_subscription_ids(self.artist.pk, self.now),
            [],
        )

    def test_renewal_uses_latest_confirmed_payment(self):
        self.payment(
            fulfilled_at=self.now - timedelta(days=40)
        )

        self.payment(fulfilled_at=self.now)

        period = subscription_periods(
            self.artist.pk, self.now
        )[self.plan.pk]

        self.assertTrue(period["active"])

        self.assertEqual(
            period["expires_at"],
            self.now + timedelta(days=30),
        )

    def test_legacy_relation_without_payment_is_not_active(self):
        self.artist_profile.sus.add(self.plan)

        self.assertEqual(
            active_subscription_ids(self.artist.pk, self.now),
            [],
        )
