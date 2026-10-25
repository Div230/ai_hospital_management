from django.db import models
from core.models import BaseModel


class Pharmacy(BaseModel):
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='pharmacy_profile',
        limit_choices_to={'role': 'pharmacy'},
    )
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Medicine(BaseModel):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    manufacturer = models.CharField(max_length=150, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=30, default='tablet')
    requires_prescription = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['pharmacy', 'name'])]

    def __str__(self):
        return f'{self.name} - {self.pharmacy}'

    @property
    def in_stock(self):
        return self.stock_quantity > 0


class MedicineOrder(BaseModel):
    STATUS_CHOICES = (
        ('PLACED', 'Placed'), ('CONFIRMED', 'Confirmed'), ('PACKED', 'Packed'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'), ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled'),
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='medicine_orders')
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='orders')
    prescription = models.ForeignKey(
        'appointments.Prescription', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.TextField(blank=True)

    # payment kept as demo/mock only per project scope
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'Order {self.id} - {self.patient}'


class MedicineOrderItem(BaseModel):
    order = models.ForeignKey(MedicineOrder, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='+')
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f'{self.medicine.name} x{self.quantity}'
